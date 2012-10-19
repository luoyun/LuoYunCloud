/*
    COLLECTION LIBRARY

    Implementation of the collection library interface.

    Copyright (C) Dmitri Pal <dpal@redhat.com> 2009

    Collection Library is free software: you can redistribute it and/or modify
    it under the terms of the GNU Lesser General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Collection Library is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Lesser General Public License for more details.

    You should have received a copy of the GNU Lesser General Public License
    along with Collection Library.  If not, see <http://www.gnu.org/licenses/>.
*/

#define _GNU_SOURCE
#include <string.h>
#include <stdlib.h>
#include <errno.h>
#include <ctype.h>
#include <time.h>
#include "config.h"
#include "trace.h"

/* The collection should use the real structures */
#include "collection_priv.h"
#include "collection.h"


/* Internal constants defined to denote actions that can be performed by find handler */
#define COLLECTION_ACTION_FIND       1
#define COLLECTION_ACTION_DEL        2
#define COLLECTION_ACTION_UPDATE     3
#define COLLECTION_ACTION_GET        4


/* Special internal error code to indicate that collection search was interrupted */
#define EINTR_INTERNAL 10000


/* Potential subject for management with libtools */
#define DATE_FORMAT "%c"

#define TIME_ARRAY_SIZE 100

/* Magic numbers for hashing */
#if SIZEOF_LONG == 8
    #define FNV1a_prime 1099511628211ul
    #define FNV1a_base 14695981039346656037ul
#elif SIZEOF_LONG_LONG == 8
    #define FNV1a_prime 1099511628211ull
    #define FNV1a_base 14695981039346656037ull
#else
    #error "Platform cannot support 64-bit constant integers"
#endif

/* Struct used for passing parameter for update operation */
struct update_property {
        int type;
        void *data;
        int length;
        int found;
};

/* This struct is used to construct path
 * to an item in the collection (tree)
 */
struct path_data {
    char *name;
    int length;
    struct path_data *previous_path;
};

/* Structure to keep data needed to
 * copy collection
 * while traversing it
 */
struct col_copy {
    int mode;
    struct path_data *current_path;
    char *given_name;
    int given_len;
    col_copy_cb copy_cb;
    void *ext_data;
};

/******************** FUNCTION DECLARATIONS ****************************/

/* Have to declare those due to function cross referencing */
static int col_find_item_and_do(struct collection_item *ci,
                                const char *property_to_find,
                                int type,
                                int mode_flags,
                                col_item_fn item_handler,
                                void *custom_data,
                                int action);

/* Traverse callback for find & delete function */
static int col_act_traverse_handler(struct collection_item *head,
                                    struct collection_item *previous,
                                    struct collection_item *current,
                                    void *passed_traverse_data,
                                    col_item_fn user_item_handler,
                                    void *custom_data,
                                    int *stop);

/* Traverse handler to find parent of the item */
static int col_parent_traverse_handler(struct collection_item *head,
                                       struct collection_item *previous,
                                       struct collection_item *current,
                                       void *traverse_data,
                                       col_item_fn user_item_handler,
                                       void *custom_data,
                                       int *stop);

/* Traverse callback signature */
typedef int (*internal_item_fn)(struct collection_item *head,
                                struct collection_item *previous,
                                struct collection_item *current,
                                void *traverse_data,
                                col_item_fn user_item_handler,
                                void *custom_data,
                                int *stop);
/* Function to walk_items */
static int col_walk_items(struct collection_item *ci,
                          int mode_flags,
                          internal_item_fn traverse_handler,
                          void *traverse_data,
                          col_item_fn user_item_handler,
                          void *custom_data,
                          unsigned *depth);

/* Function to get sub collection */
static int col_get_subcollection(const char *property,
                                  int property_len,
                                  int type,
                                  void *data,
                                  int length,
                                  void *found,
                                  int *dummy);

/* Function to destroy collection */
void col_destroy_collection(struct collection_item *ci);

/******************** SUPPLEMENTARY FUNCTIONS ****************************/
/* BASIC OPERATIONS */

/* Function that checks if property can be added */
static int col_validate_property(const char *property)
{
    TRACE_FLOW_STRING("col_validate_property", "Entry point.");
    /* Only alpha numeric characters are allowed in names of the properties */
    int invalid = 0;
    const char *check;

    check = property;
    while (*check != '\0') {
        /* It turned out that limiting collection charcters is bad */
        if ((*check < ' ') || (*check == '!')) {
            invalid = 1;
            break;
        }
        check++;
    }
    TRACE_FLOW_NUMBER("col_validate_property. Returning ", invalid);
    return invalid;
}

/* Function that cleans the item */
void col_delete_item(struct collection_item *item)
{
    struct collection_item *other_collection;

    TRACE_FLOW_STRING("col_delete_item","Entry point.");

    if (item == NULL) {
        TRACE_FLOW_STRING("col_delete_item","Nothing to delete!");
        return;
    }

    /* Handle external or embedded collection */
    if(item->type == COL_TYPE_COLLECTIONREF)  {
        /* Our data is a pointer to a whole external collection so dereference
         * it or delete */
        other_collection = *((struct collection_item **)(item->data));
        col_destroy_collection(other_collection);
    }

    TRACE_INFO_STRING("Deleting property:", item->property);
    TRACE_INFO_NUMBER("Type:", item->type);

    if (item->property != NULL) free(item->property);
    if (item->data != NULL) free(item->data);

    free(item);

    TRACE_FLOW_STRING("col_delete_item","Exit.");
}

/* A generic function to allocate a property item */
int col_allocate_item(struct collection_item **ci, const char *property,
                      const void *item_data, int length, int type)
{
    struct collection_item *item = NULL;

    TRACE_FLOW_STRING("col_allocate_item", "Entry point.");
    TRACE_INFO_NUMBER("Will be using type:", type);

    /* Check the length */
    if (length >= COL_MAX_DATA) {
        TRACE_ERROR_STRING("col_allocate_item", "Data to long.");
        return EMSGSIZE;
    }

    if (col_validate_property(property)) {
        TRACE_ERROR_STRING("Invalid chracters in the property name", property);
        return EINVAL;
    }

    /* Allocate memory for the structure */
    item = (struct collection_item *)malloc(sizeof(struct collection_item));
    if (item == NULL)  {
        TRACE_ERROR_STRING("col_allocate_item", "Malloc failed.");
        return ENOMEM;
    }

    /* After we initialize members we can use delete_item() in case of error */
    item->next = NULL;
    item->property = NULL;
    item->data = NULL;
    TRACE_INFO_NUMBER("About to set type to:", type);
    item->type = type;

    /* Copy property */
    item->property = strdup(property);
    if (item->property == NULL) {
        TRACE_ERROR_STRING("col_allocate_item", "Failed to dup property.");
        col_delete_item(item);
        return ENOMEM;
    }

    item->phash = col_make_hash(property, 0, &(item->property_len));
    TRACE_INFO_NUMBER("Item hash", item->phash);
    TRACE_INFO_NUMBER("Item property length", item->property_len);
    TRACE_INFO_NUMBER("Item property strlen", strlen(item->property));

    /* Deal with data */
    item->data = malloc(length);
    if (item->data == NULL) {
        TRACE_ERROR_STRING("col_allocate_item", "Failed to dup data.");
        col_delete_item(item);
        return ENOMEM;
    }

    memcpy(item->data, item_data, length);
    item->length = length;

    /* Make sure that data is NULL terminated in case of string */
    if (type == COL_TYPE_STRING) ((char *)(item->data))[length-1] = '\0';

    *ci = item;

    TRACE_INFO_STRING("Item property", item->property);
    TRACE_INFO_NUMBER("Item property type", item->type);
    TRACE_INFO_NUMBER("Item data length", item->length);
    TRACE_FLOW_STRING("col_allocate_item", "Success exit.");
    return EOK;
}

/* Structure used to find things in collection */
struct property_search {
    const char *property;
    uint64_t hash;
    struct collection_item *parent;
    int index;
    int count;
    int found;
    int use_type;
    int type;
};

/* Find the parent of the item with given name */
static int col_find_property(struct collection_item *collection,
                             const char *refprop,
                             int idx,
                             int use_type,
                             int type,
                             struct collection_item **parent)
{
    struct property_search ps;
    int i = 0;
    unsigned depth = 0;

    TRACE_FLOW_STRING("col_find_property", "Entry.");

    *parent = NULL;

    ps.property = refprop;
    ps.hash = FNV1a_base;
    ps.parent = NULL;
    ps.index = idx;
    ps.count = 0;
    ps.found = 0;
    ps.use_type = use_type;
    ps.type = type;

    /* Create hash of the string to search */
    while(refprop[i] != 0) {
        ps.hash = ps.hash ^ toupper(refprop[i]);
        ps.hash *= FNV1a_prime;
        i++;
    }

    /* We do not care about error here */
    (void)col_walk_items(collection, COL_TRAVERSE_ONELEVEL,
                         col_parent_traverse_handler,
                         (void *)parent, NULL, (void *)&ps,
                         &depth);

    if (*parent) {
        /* Item is found in the collection */
        TRACE_FLOW_STRING("col_find_property", "Exit - item found");
        return 1;
    }

    /* Item is not found */
    TRACE_FLOW_STRING("col_find_property", "Exit - item NOT found");
    return EOK;
}



/* Insert item into the current collection */
int col_insert_item_into_current(struct collection_item *collection,
                                 struct collection_item *item,
                                 int disposition,
                                 const char *refprop,
                                 int idx,
                                 unsigned flags)
{
    struct collection_header *header = NULL;
    struct collection_item *parent = NULL;
    struct collection_item *current = NULL;
    int refindex = 0;

    TRACE_FLOW_STRING("col_insert_item_into_current", "Entry point");

    /* Do best effort on the item */
    if ((!item) || (item->next)) {
        TRACE_ERROR_STRING("Passed in item is invalid", "");
        return EINVAL;
    }

    if (collection == NULL) {
        TRACE_INFO_STRING("col_insert_item_into_current",
                          "Collection accepting is NULL");
        if (item->type == COL_TYPE_COLLECTION) {
            /* This is a special case of self creation */
            TRACE_INFO_STRING("col_insert_item_into_current",
                              "Adding header item to new collection.");
            collection = item;
        }
        else {
            TRACE_ERROR_STRING("Passed in item is invalid", "");
            return EINVAL;
        }
    }
    else {
        /* We can add items only to collections */
        if (collection->type != COL_TYPE_COLLECTION) {
            TRACE_ERROR_STRING("Attempt to add item to non collection.","");
            TRACE_ERROR_STRING("Collection name:", collection->property);
            TRACE_ERROR_NUMBER("Collection type:", collection->type);
            return EINVAL;
        }
    }

    /* After processing flags we can process disposition */

    header = (struct collection_header *)collection->data;

    /* Check flags first */
    switch(flags) {
    case COL_INSERT_NOCHECK:    /* No check - good just fall through */
                                TRACE_INFO_STRING("Insert without check", "");
                                break;
    case COL_INSERT_DUPOVER:    /* Find item and overwrite - ignore disposition */
                                if (col_find_property(collection, item->property, 0, 0, 0, &parent)) {
                                    current = parent->next;
                                    item->next = current->next;
                                    parent->next = item;
                                    if (header->last == current) header->last = item;
                                    col_delete_item(current);
                                    /* Deleted one added another - count stays the same! */
                                    TRACE_FLOW_STRING("col_insert_item_into_current", "Dup overwrite exit");
                                    return EOK;
                                }
                                /* Not found so we fall thorough and add as requested */
                                break;

    case COL_INSERT_DUPOVERT:   /* Find item by name and type and overwrite - ignore disposition */
                                if (col_find_property(collection, item->property, 0, 1, item->type, &parent)) {
                                    current = parent->next;
                                    item->next = current->next;
                                    parent->next = item;
                                    if (header->last == current) header->last = item;
                                    col_delete_item(current);
                                    /* Deleted one added another - count stays the same! */
                                    TRACE_FLOW_STRING("col_insert_item_into_current", "Dup overwrite exit");
                                    return EOK;
                                }
                                /* Not found so we fall thorough and add as requested */
                                break;

    case COL_INSERT_DUPERROR:   if (col_find_property(collection, item->property, 0, 0, 0, &parent)) {
                                    /* Return error */
                                    TRACE_ERROR_NUMBER("Duplicate property", EEXIST);
                                    return EEXIST;
                                }
                                break;

    case COL_INSERT_DUPERRORT:  if (col_find_property(collection, item->property, 0, 1, item->type, &parent)) {
                                    /* Return error */
                                    TRACE_ERROR_NUMBER("Duplicate property of the same type", EEXIST);
                                    return EEXIST;
                                }
                                break;

    case COL_INSERT_DUPMOVE:    /* Find item and delete */
                                if (col_find_property(collection, item->property, 0, 0, 0, &parent)) {
                                    current = parent->next;
                                    parent->next = current->next;
                                    if (header->last == current) header->last = parent;
                                    col_delete_item(current);
                                    header->count--;
                                }
                                /* Now add item according to the disposition */
                                break;

    case COL_INSERT_DUPMOVET:   /* Find item and delete */
                                TRACE_INFO_STRING("Property:", item->property);
                                TRACE_INFO_NUMBER("Type:", item->type);
                                if (col_find_property(collection, item->property, 0, 1, item->type, &parent)) {
                                    TRACE_INFO_NUMBER("Current:", (unsigned)(parent->next));
                                    current = parent->next;
                                    parent->next = current->next;
                                    if (header->last == current) header->last = parent;
                                    col_delete_item(current);
                                    header->count--;
                                }
                                /* Now add item according to the disposition */
                                break;

    default:                    /* The new ones should be added here */
                                TRACE_ERROR_NUMBER("Flag is not implemented", ENOSYS);
                                return ENOSYS;
    }


    switch (disposition) {
    case COL_DSP_END:       /* Link new item to the last item in the list if there any */
                            if (header->count != 0) header->last->next = item;
                            /* Make sure we save a new last element */
                            header->last = item;
                            header->count++;
                            break;

    case COL_DSP_FRONT:     /* Same as above if there is header only */
                            if (header->count == 1) {
                                header->last->next = item;
                                header->last = item;
                            }
                            else {
                                item->next = collection->next;
                                collection->next = item;
                            }
                            header->count++;
                            break;

    case COL_DSP_BEFORE:    /* Check argument */
                            if (!refprop) {
                                TRACE_ERROR_STRING("In this case property is required", "");
                                return EINVAL;
                            }

                            /* We need to find property */
                            if (col_find_property(collection, refprop, 0, 0, 0, &parent)) {
                                item->next = parent->next;
                                parent->next = item;
                                header->count++;
                            }
                            else {
                                TRACE_ERROR_STRING("Property not found", refprop);
                                return ENOENT;
                            }
                            break;

    case COL_DSP_AFTER:     /* Check argument */
                            if (!refprop) {
                                TRACE_ERROR_STRING("In this case property is required", "");
                                return EINVAL;
                            }

                            /* We need to find property */
                            if (col_find_property(collection, refprop, 0, 0, 0, &parent)) {
                                parent = parent->next;
                                if (parent->next) {
                                    /* It is not the last item */
                                    item->next = parent->next;
                                    parent->next = item;
                                }
                                else {
                                    /* It is the last item */
                                    header->last->next = item;
                                    header->last = item;
                                }
                                header->count++;
                            }
                            else {
                                TRACE_ERROR_STRING("Property not found", refprop);
                                return ENOENT;
                            }
                            break;

    case COL_DSP_INDEX:     if(idx == 0) {
                                /* Same is first */
                                if (header->count == 1) {
                                    header->last->next = item;
                                    header->last = item;
                                }
                                else {
                                    item->next = collection->next;
                                    collection->next = item;
                                }
                            }
                            else if(idx >= header->count - 1) {
                                /* In this case add to the end */
                                header->last->next = item;
                                /* Make sure we save a new last element */
                                header->last = item;
                            }
                            else {
                                /* In the middle */
                                parent = collection;
                                /* Move to the right position counting */
                                while (idx > 0) {
                                    idx--;
                                    parent = parent->next;
                                }
                                item->next = parent->next;
                                parent->next = item;
                            }
                            header->count++;
                            break;

    case COL_DSP_FIRSTDUP:
    case COL_DSP_LASTDUP:
    case COL_DSP_NDUP:

                            if (disposition == COL_DSP_FIRSTDUP) refindex = 0;
                            else if (disposition == COL_DSP_LASTDUP) refindex = -1;
                            else refindex = idx;

                            /* We need to find property based on index */
                            if (col_find_property(collection, item->property, refindex, 0, 0, &parent)) {
                                item->next = parent->next;
                                parent->next = item;
                                header->count++;
                                if(header->last == parent) header->last = item;
                            }
                            else {
                                TRACE_ERROR_STRING("Property not found", refprop);
                                return ENOENT;
                            }
                            break;

    default:
                            TRACE_ERROR_STRING("Disposition is not implemented", "");
                            return ENOSYS;

    }


    TRACE_INFO_STRING("Collection:", collection->property);
    TRACE_INFO_STRING("Just added item is:", item->property);
    TRACE_INFO_NUMBER("Item type.", item->type);
    TRACE_INFO_NUMBER("Number of items in collection now is.", header->count);

    TRACE_FLOW_STRING("col_insert_item_into_current", "Exit");
    return EOK;
}

/* Extract item from the current collection */
int col_extract_item_from_current(struct collection_item *collection,
                                  int disposition,
                                  const char *refprop,
                                  int idx,
                                  int type,
                                  struct collection_item **ret_ref)
{
    struct collection_header *header = NULL;
    struct collection_item *parent = NULL;
    struct collection_item *current = NULL;
    struct collection_item *found = NULL;
    int refindex = 0;
    int use_type = 0;

    TRACE_FLOW_STRING("col_extract_item_from_current", "Entry point");

    /* Check that collection is not empty */
    if ((collection == NULL) || (collection->type != COL_TYPE_COLLECTION)) {
        TRACE_ERROR_STRING("Collection can't be NULL", "");
        return EINVAL;
    }

    header = (struct collection_header *)collection->data;

    /* Before moving forward we need to check if there is anything to extract */
    if (header->count <= 1) {
        TRACE_ERROR_STRING("Collection is empty.", "Nothing to extract.");
        return ENOENT;
    }

    if (type != 0) use_type = 1;

    switch (disposition) {
    case COL_DSP_END:       /* Extract last item in the list. */
                            parent = collection;
                            current = collection->next;
                            while (current->next != NULL) {
                                parent = current;
                                current = current->next;
                            }
                            *ret_ref = parent->next;
                            parent->next = NULL;
                            /* Special case - one data element */
                            if (header->count == 2) header->last = collection;
                            else header->last = parent;
                            break;

    case COL_DSP_FRONT:     /* Extract first item in the list */
                            *ret_ref = collection->next;
                            collection->next = (*ret_ref)->next;
                            /* Special case - one data element */
                            if (header->count == 2) header->last = collection;
                            break;

    case COL_DSP_BEFORE:    /* Check argument */
                            if (!refprop) {
                                TRACE_ERROR_STRING("In this case property is required", "");
                                return EINVAL;
                            }

                            /* We have to do it in two steps */
                            /* First find the property that is mentioned */
                            if (col_find_property(collection, refprop, 0, use_type, type, &found)) {
                                /* We found the requested property */
                                if (found->next == collection->next) {
                                    /* The referenced property is the first in the list */
                                    TRACE_ERROR_STRING("Nothing to extract. Lists starts with property", refprop);
                                    return ENOENT;
                                }
                                /* Get to the parent of the item that is before the one that is found */
                                parent = collection;
                                current = collection->next;
                                while (current != found) {
                                    parent = current;
                                    current = current->next;
                                }
                                *ret_ref = current;
                                parent->next = current->next;

                            }
                            else {
                                TRACE_ERROR_STRING("Property not found", refprop);
                                return ENOENT;
                            }
                            break;

    case COL_DSP_AFTER:     /* Check argument */
                            if (!refprop) {
                                TRACE_ERROR_STRING("In this case property is required", "");
                                return EINVAL;
                            }

                            /* We need to find property */
                            if (col_find_property(collection, refprop, 0, use_type, type, &parent)) {
                                current = parent->next;
                                if (current->next) {
                                    *ret_ref = current->next;
                                    current->next = (*ret_ref)->next;
                                    /* If we removed the last element adjust header */
                                    if(current->next == NULL) header->last = current;
                                }
                                else {
                                    TRACE_ERROR_STRING("Property is last in the list", refprop);
                                    return ENOENT;
                                }
                            }
                            else {
                                TRACE_ERROR_STRING("Property not found", refprop);
                                return ENOENT;
                            }
                            break;

    case COL_DSP_INDEX:     if (idx == 0) {
                                *ret_ref = collection->next;
                                collection->next = (*ret_ref)->next;
                                /* Special case - one data element */
                                if (header->count == 2) header->last = collection;
                            }
                            /* Index 0 stands for the first data element.
                             * Count includes header element.
                             */
                            else if (idx >= (header->count - 1)) {
                                TRACE_ERROR_STRING("Index is out of boundaries", refprop);
                                return ENOENT;
                            }
                            else {
                                /* Loop till the element with right index */
                                refindex = 0;
                                parent = collection;
                                current = collection->next;
                                while (refindex < idx) {
                                    parent = current;
                                    current = current->next;
                                    refindex++;
                                }
                                *ret_ref = parent->next;
                                parent->next = (*ret_ref)->next;
                                /* If we removed the last element adjust header */
                                if (parent->next == NULL) header->last = parent;
                            }
                            break;

    case COL_DSP_FIRSTDUP:
    case COL_DSP_LASTDUP:
    case COL_DSP_NDUP:

                            if (disposition == COL_DSP_FIRSTDUP) refindex = 0;
                            else if (disposition == COL_DSP_LASTDUP) refindex = -2;
                            else refindex = idx;

                            /* We need to find property based on index */
                            if (col_find_property(collection, refprop, refindex, use_type, type, &parent)) {
                                *ret_ref = parent->next;
                                parent->next = (*ret_ref)->next;
                                /* If we removed the last element adjust header */
                                if(parent->next == NULL) header->last = parent;
                            }
                            else {
                                TRACE_ERROR_STRING("Property not found", refprop);
                                return ENOENT;
                            }
                            break;

    default:
                            TRACE_ERROR_STRING("Disposition is not implemented", "");
                            return ENOSYS;

    }


    /* Clear item and reduce count */
    (*ret_ref)->next = NULL;
    header->count--;

    TRACE_INFO_STRING("Collection:", (*ret_ref)->property);
    TRACE_INFO_NUMBER("Item type.", (*ret_ref)->type);
    TRACE_INFO_NUMBER("Number of items in collection now is.", header->count);

    TRACE_FLOW_STRING("col_extract_item_from_current", "Exit");
    return EOK;
}

/* Extract item from the collection */
int col_extract_item(struct collection_item *collection,
                     const char *subcollection,
                     int disposition,
                     const char *refprop,
                     int idx,
                     int type,
                     struct collection_item **ret_ref)
{
    struct collection_item *col = NULL;
    int error = EOK;

    TRACE_FLOW_STRING("col_extract_item", "Entry point");

    /* Check that collection is not empty */
    if ((collection == NULL) || (collection->type != COL_TYPE_COLLECTION)) {
        TRACE_ERROR_STRING("Collection can't be NULL", "");
        return EINVAL;
    }

    /* Get subcollection if needed */
    if (subcollection == NULL) {
        col = collection;
    }
    else {
        TRACE_INFO_STRING("Subcollection id not null, searching", subcollection);
        error = col_find_item_and_do(collection, subcollection,
                                     COL_TYPE_COLLECTIONREF,
                                     COL_TRAVERSE_DEFAULT,
                                     col_get_subcollection, (void *)(&col),
                                     COLLECTION_ACTION_FIND);
        if (error) {
            TRACE_ERROR_NUMBER("Search for subcollection returned error:", error);
            return error;
        }

        if (col == NULL) {
            TRACE_ERROR_STRING("Search for subcollection returned NULL pointer", "");
            return ENOENT;
        }

    }

    /* Extract from the current collection */
    error = col_extract_item_from_current(col,
                                          disposition,
                                          refprop,
                                          idx,
                                          type,
                                          ret_ref);
    if (error) {
        TRACE_ERROR_NUMBER("Failed to extract item from the current collection", error);
        return error;
    }

    TRACE_FLOW_STRING("col_extract_item", "Exit");
    return EOK;
}


/* Remove item (property) from collection.*/
int col_remove_item(struct collection_item *ci,
                    const char *subcollection,
                    int disposition,
                    const char *refprop,
                    int idx,
                    int type)
{
    int error = EOK;
    struct collection_item *ret_ref = NULL;

    TRACE_FLOW_STRING("col_remove_item", "Exit");

    /* Extract from the current collection */
    error = col_extract_item(ci,
                             subcollection,
                             disposition,
                             refprop,
                             idx,
                             type,
                             &ret_ref);
    if (error) {
        TRACE_ERROR_NUMBER("Failed to extract item from the collection", error);
        return error;
    }

    col_delete_item(ret_ref);

    TRACE_FLOW_STRING("col_remove_item", "Exit");
    return EOK;
}

/* Remove item (property) from current collection.
 * Just a simple wrapper.
 */
int col_remove_item_from_current(struct collection_item *ci,
                                 int disposition,
                                 const char *refprop,
                                 int idx,
                                 int type)
{
    int error = EOK;

    TRACE_FLOW_STRING("col_remove_item_from_current", "Exit");

    /* Remove item from current collection */
    error = col_remove_item(ci,
                            NULL,
                            disposition,
                            refprop,
                            idx,
                            type);

    TRACE_FLOW_NUMBER("col_remove_item_from_current. Exit. Returning", error);
    return error;
}


/* Insert the item into the collection or subcollection */
int col_insert_item(struct collection_item *collection,
                    const char *subcollection,
                    struct collection_item *item,
                    int disposition,
                    const char *refprop,
                    int idx,
                    unsigned flags)
{
    int error;
    struct collection_item *acceptor = NULL;

    TRACE_FLOW_STRING("col_insert_item", "Entry point.");

    /* Do best effort on the item */
    if ((!item) || (item->next)) {
        TRACE_ERROR_STRING("Passed in item is invalid", "");
        return EINVAL;
    }

    /* Check that collection is not empty */
    if ((collection == NULL) && (item->type != COL_TYPE_COLLECTION)) {
        TRACE_ERROR_STRING("Collection can't be NULL", "");
        return EINVAL;
    }

    /* Add item to collection */
    if (subcollection == NULL) {
        acceptor = collection;
    }
    else {
        TRACE_INFO_STRING("Subcollection id not null, searching", subcollection);
        error = col_find_item_and_do(collection, subcollection,
                                     COL_TYPE_COLLECTIONREF,
                                     COL_TRAVERSE_DEFAULT,
                                     col_get_subcollection, (void *)(&acceptor),
                                     COLLECTION_ACTION_FIND);
        if (error) {
            TRACE_ERROR_NUMBER("Search for subcollection returned error:", error);
            return error;
        }

        if (acceptor == NULL) {
            TRACE_ERROR_STRING("Search for subcollection returned NULL pointer", "");
            return ENOENT;
        }

    }

    /* Instert item to the current collection */
    error = col_insert_item_into_current(acceptor,
                                         item,
                                         disposition,
                                         refprop,
                                         idx,
                                         flags);

    if (error) {
        TRACE_ERROR_NUMBER("Failed to insert item into current collection", error);
        return error;
    }

    TRACE_FLOW_STRING("insert_item", "Exit");
    return EOK;
}


/* Insert property with reference.
 * This is internal function so we do not check parameters.
 * See external wrapper below.
 */
static int col_insert_property_with_ref_int(struct collection_item *collection,
                                            const char *subcollection,
                                            int disposition,
                                            const char *refprop,
                                            int idx,
                                            unsigned flags,
                                            const char *property,
                                            int type,
                                            const void *data,
                                            int length,
                                            struct collection_item **ret_ref)
{
    struct collection_item *item = NULL;
    int error;

    TRACE_FLOW_STRING("col_insert_property_with_ref_int", "Entry point.");

    /* Create a new property out of the given parameters */
    error = col_allocate_item(&item, property, data, length, type);
    if (error) {
        TRACE_ERROR_NUMBER("Failed to allocate item", error);
        return error;
    }

    /* Send the property to the insert_item function */
    error = col_insert_item(collection,
                            subcollection,
                            item,
                            disposition,
                            refprop,
                            idx,
                            flags);
    if (error) {
        TRACE_ERROR_NUMBER("Failed to insert item", error);
        col_delete_item(item);
        return error;
    }

    if (ret_ref) *ret_ref = item;

    TRACE_FLOW_STRING("col_insert_property_with_ref_int", "Exit");
    return EOK;
}

/* Special function used to copy item from one
 * collection to another using caller's callback.
 */
static int col_copy_item_with_cb(struct collection_item *collection,
                                 const char *property,
                                 int type,
                                 const void *data,
                                 int length,
                                 col_copy_cb copy_cb,
                                 void *ext_data)
{
    struct collection_item *item = NULL;
    int skip = 0;
    int error = EOK;

    TRACE_FLOW_STRING("col_copy_item_with_cb", "Entry point.");

    /* Create a new property out of the given parameters */
    error = col_allocate_item(&item, property, data, length, type);
    if (error) {
        TRACE_ERROR_NUMBER("Failed to allocate item", error);
        return error;
    }

    /* Call callback if any */
    if (copy_cb) {
        TRACE_INFO_STRING("Calling callback for item:", item->property);
        error = copy_cb(item, ext_data, &skip);
        if (error) {
            TRACE_ERROR_NUMBER("Callback failed", error);
            col_delete_item(item);
            return error;
        }
    }

    /* Are we told to skip this item? */
    if (skip) col_delete_item(item);
    else {
        /* Insted property into the collection */
        error = col_insert_item(collection,
                                NULL,
                                item,
                                COL_DSP_END,
                                NULL,
                                0,
                                0);
        if (error) {
            TRACE_ERROR_NUMBER("Failed to insert item", error);
            col_delete_item(item);
            return error;
        }
    }

    TRACE_FLOW_STRING("col_copy_item_with_cb", "Exit");
    return EOK;
}


/* This is public function so we need to check the validity
 * of the arguments.
 */
int col_insert_property_with_ref(struct collection_item *collection,
                                 const char *subcollection,
                                 int disposition,
                                 const char *refprop,
                                 int idx,
                                 unsigned flags,
                                 const char *property,
                                 int type,
                                 const void *data,
                                 int length,
                                 struct collection_item **ret_ref)
{
    int error;

    TRACE_FLOW_STRING("col_insert_property_with_ref", "Entry point.");

    /* Check that collection is not empty */
    if (collection == NULL) {
        TRACE_ERROR_STRING("Collection cant be NULL", "");
        return EINVAL;
    }

    error = col_insert_property_with_ref_int(collection,
                                             subcollection,
                                             disposition,
                                             refprop,
                                             idx,
                                             flags,
                                             property,
                                             type,
                                             data,
                                             length,
                                             ret_ref);

    TRACE_FLOW_NUMBER("col_insert_property_with_ref_int Returning:", error);
    return error;
}
/* TRAVERSE HANDLERS */

/* Special handler to just set a flag if the item is found */
static int col_is_in_item_handler(const char *property,
                                  int property_len,
                                  int type,
                                  void *data,
                                  int length,
                                  void *found,
                                  int *dummy)
{
    TRACE_FLOW_STRING("col_is_in_item_handler", "Entry.");
    TRACE_INFO_STRING("Property:", property);
    TRACE_INFO_NUMBER("Property length:", property_len);
    TRACE_INFO_NUMBER("Type:", type);
    TRACE_INFO_NUMBER("Length:", length);

    *((int *)(found)) = COL_MATCH;

    TRACE_FLOW_STRING("col_is_in_item_handler", "Success Exit.");

    return EOK;
}

/* Special handler to retrieve the sub collection */
static int col_get_subcollection(const char *property,
                                 int property_len,
                                 int type,
                                 void *data,
                                 int length,
                                 void *found,
                                 int *dummy)
{
    TRACE_FLOW_STRING("col_get_subcollection", "Entry.");
    TRACE_INFO_STRING("Property:", property);
    TRACE_INFO_NUMBER("Property length:", property_len);
    TRACE_INFO_NUMBER("Type:", type);
    TRACE_INFO_NUMBER("Length:", length);

    *((struct collection_item **)(found)) = *((struct collection_item **)(data));

    TRACE_FLOW_STRING("col_get_subcollection","Success Exit.");

    return EOK;

}



/* CLEANUP */

/* Cleans the collection tree including current item. */
/* The passed in variable should not be used after the call
 * as memory is freed!!! */
static void col_delete_collection(struct collection_item *ci)
{
    TRACE_FLOW_STRING("col_delete_collection", "Entry.");

    if (ci == NULL) {
        TRACE_FLOW_STRING("col_delete_collection", "Nothing to do Exit.");
        return;
    }

    TRACE_INFO_STRING("Real work to do", "");
    TRACE_INFO_STRING("Property", ci->property);
    TRACE_INFO_NUMBER("Next item", ci->next);

    col_delete_collection(ci->next);

    /* Delete this item */
    col_delete_item(ci);
    TRACE_FLOW_STRING("col_delete_collection", "Exit.");
}


/* NAME MANAGEMENT - used by search */

/* Internal data structures used for search */


struct find_name {
    const char *name_to_find;
    int name_len_to_find;
    uint64_t hash;
    int type_to_match;
    char *given_name;
    int given_len;
    struct path_data *current_path;
    int action;
};

/* Create a new name */
static int col_create_path_data(struct path_data **name_path,
                                const char *name, int length,
                                const char *property, int property_len,
                                char sep)
{
    int error = EOK;
    struct path_data *new_name_path;

    TRACE_FLOW_STRING("col_create_path_data", "Entry.");

    TRACE_INFO_STRING("Constructing path from name:", name);
    TRACE_INFO_STRING("Constructing path from property:", property);

    /* Allocate structure */
    new_name_path = (struct path_data *)malloc(sizeof(struct path_data));
    if (new_name_path == NULL) {
        TRACE_ERROR_NUMBER("Failed to allocate memory for new path struct.", ENOMEM);
        return ENOMEM;
    }
    new_name_path->name = malloc(length + property_len + 2);
    if (new_name_path->name == NULL) {
        TRACE_ERROR_NUMBER("Failed to allocate memory for new path name.", ENOMEM);
        free(new_name_path);
        return ENOMEM;
    }

    /* Construct the new name */
    new_name_path->length = 0;

    if(length > 0) {
        memcpy(new_name_path->name, name, length);
        new_name_path->length = length;
        new_name_path->name[new_name_path->length] = sep;
        new_name_path->length++;
        new_name_path->name[new_name_path->length] = '\0';
        TRACE_INFO_STRING("Name so far:", new_name_path->name);
        TRACE_INFO_NUMBER("Len so far:", new_name_path->length);
    }
    memcpy(&new_name_path->name[new_name_path->length], property, property_len);
    new_name_path->length += property_len;
    new_name_path->name[new_name_path->length] = '\0';

    /* Link to the chain */
    new_name_path->previous_path = *name_path;
    *name_path = new_name_path;

    TRACE_INFO_STRING("Constructed path", new_name_path->name);


    TRACE_FLOW_NUMBER("col_create_path_data. Returning:", error);
    return error;
}

/* Matching item name and type */
static int col_match_item(struct collection_item *current,
                          struct find_name *traverse_data)
{

    const char *find_str;
    const char *start;
    const char *data_str;

    TRACE_FLOW_STRING("col_match_item", "Entry");

    if (traverse_data->type_to_match & current->type) {

        /* Check if there is any value to match */
        if ((traverse_data->name_to_find == NULL) ||
            (*(traverse_data->name_to_find) == '\0')) {
            TRACE_INFO_STRING("col_match_item",
                              "Returning MATCH because there is no search criteria!");
            return COL_MATCH;
        }

        /* Check the hashes - if they do not match return */
        if (traverse_data->hash != current->phash) {
            TRACE_INFO_STRING("col_match_item","Returning NO match!");
            return COL_NOMATCH;
        }

        /* We will do the actual string comparison only if the hashes matched */

        /* Start comparing the two strings from the end */
        find_str = traverse_data->name_to_find + traverse_data->name_len_to_find;
        start = current->property;
        data_str = start + current->property_len;

        TRACE_INFO_STRING("Searching for:", traverse_data->name_to_find);
        TRACE_INFO_STRING("Item name:", current->property);
        TRACE_INFO_STRING("Current path:", traverse_data->current_path->name);
        TRACE_INFO_NUMBER("Searching:", toupper(*find_str));
        TRACE_INFO_NUMBER("Have:", toupper(*data_str));

        /* We start pointing to 0 so the loop will be executed at least once */
        while (toupper(*data_str) == toupper(*find_str)) {

            TRACE_INFO_STRING("Loop iteration:","");

            if (data_str == start) {
                if (find_str > traverse_data->name_to_find) {
                    if (*(find_str-1) == '!') {
                        /* We matched the property but the search string is
                         * longer so we need to continue matching */
                        TRACE_INFO_STRING("col_match_item",
                                          "Need to continue matching");
                        start = traverse_data->current_path->name;
                        data_str = &start[traverse_data->current_path->length - 1];
                        find_str -= 2;
                        continue;
                    }
                    else {
                        TRACE_INFO_STRING("col_match_item","Returning NO match!");
                        return COL_NOMATCH;
                    }
                }
                else {
                    TRACE_INFO_STRING("col_match_item","Returning MATCH!");
                    return COL_MATCH;
                }
            }
            else if ((find_str == traverse_data->name_to_find) &&
                     (*(data_str-1) == '!')) return COL_MATCH;

            data_str--;
            find_str--;
            TRACE_INFO_NUMBER("Searching:", toupper(*find_str));
            TRACE_INFO_NUMBER("Have:", toupper(*data_str));

        }
    }

    TRACE_FLOW_STRING("col_match_item","Returning NO match!");
    return COL_NOMATCH;

}

/* Function to delete the data that contains search path */
static void col_delete_path_data(struct path_data *path)
{
    TRACE_FLOW_STRING("col_delete_path_data","Entry.");

    if (path != NULL) {
        TRACE_INFO_STRING("col_delete_path_data", "Item to delete exits.");
        if (path->previous_path != NULL) {
            TRACE_INFO_STRING("col_delete_path_data",
                              "But previous item to delete exits to. Nesting.");
            col_delete_path_data(path->previous_path);
        }
        if (path->name != NULL) {
            TRACE_INFO_STRING("col_delete_path_data Deleting path:", path->name);
            free(path->name);
        }
        TRACE_INFO_STRING("col_delete_path_data", "Deleting path element");
        free(path);
    }
    TRACE_FLOW_STRING("col_delete_path_data", "Exit");
}


/* MAIN TRAVERSAL FUNCTION */

/* Internal function to walk collection */
/* For each item walked it will call traverse handler.
   Traverse handler accepts: current item,
   user provided item handler and user provided custom data. */
/* See below different traverse handlers for different cases */
static int col_walk_items(struct collection_item *ci,
                          int mode_flags,
                          internal_item_fn traverse_handler,
                          void *traverse_data,
                          col_item_fn user_item_handler,
                          void *custom_data,
                          unsigned *depth)
{
    struct collection_item *current;
    struct collection_item *parent = NULL;
    struct collection_item *sub;
    int stop = 0;
    int error = EOK;

    TRACE_FLOW_STRING("col_walk_items", "Entry.");
    TRACE_INFO_NUMBER("Mode flags:", mode_flags);

    /* Increase depth */
    /* NOTE: The depth is increased at the entry to the function.
     * and decreased right before the exit so it is safe to decrease it.
     */
    (*depth)++;

    current = ci;

    while (current) {

        TRACE_INFO_STRING("Processing item:", current->property);
        TRACE_INFO_NUMBER("Item type:", current->type);

        if (current->type == COL_TYPE_COLLECTIONREF) {

            TRACE_INFO_STRING("Subcollection:", current->property);

            if ((mode_flags & COL_TRAVERSE_IGNORE) == 0) {

                TRACE_INFO_STRING("Subcollection is not ignored.", "");
                /* We are not ignoring sub collections */

                if ((mode_flags & COL_TRAVERSE_FLAT) == 0) {

                    TRACE_INFO_STRING("Subcollection is not flattened.", "");
                    /* We are not flattening sub collections.
                     * The flattening means that we are not going
                     * to return reference and headers for sub collections.
                     * We will also not do special end collection
                     * invocation for sub collections.
                     */
                    error = traverse_handler(ci, parent, current, traverse_data,
                                             user_item_handler, custom_data, &stop);
                    if (stop != 0) {
                        TRACE_INFO_STRING("Traverse handler returned STOP.", "");
                        error = EINTR_INTERNAL;
                    }
                    /* Check what error we got */
                    if (error == EINTR_INTERNAL) {
                        TRACE_FLOW_NUMBER("Internal error - means we are stopping.", error);
                        (*depth)--;
                        return error;
                    }
                    else if (error) {
                        TRACE_ERROR_NUMBER("Traverse handler returned error.", error);
                        (*depth)--;
                        return error;
                    }
                }

                if ((mode_flags & COL_TRAVERSE_ONELEVEL) == 0) {
                    TRACE_INFO_STRING("Before diving into sub collection","");
                    sub = *((struct collection_item **)(current->data));
                    TRACE_INFO_STRING("Sub collection name", sub->property);
                    TRACE_INFO_NUMBER("Header type", sub->type);
                    /* We need to go into sub collections */
                    error = col_walk_items(sub, mode_flags,
                                           traverse_handler, traverse_data,
                                           user_item_handler, custom_data,
                                           depth);
                    TRACE_INFO_STRING("Returned from sub collection processing", "");
                    TRACE_INFO_STRING("Done processing item:", current->property);
                    TRACE_INFO_NUMBER("Done processing item type:", current->type);

                }
            }
        }
        else {
            /* Check if it is a header and we are not on the root level.
             * If we are flattening collection we need to skip headers
             * for sub collections.
             */

            /* Call handler if:
             * a) It is not collection header
             * OR
             * b) It is header we are flattening but we are on top level
             * OR
             * c) It is header and we are not flattening.
             */
            if ((current->type != COL_TYPE_COLLECTION) ||
                (((mode_flags & COL_TRAVERSE_FLAT) != 0) && (*depth == 1)) ||
                ((mode_flags & COL_TRAVERSE_FLAT) == 0)) {
                /* Call handler then move on */
                error = traverse_handler(ci, parent, current,
                                         traverse_data, user_item_handler,
                                         custom_data, &stop);

            }
        }
        /* If we are stopped - return EINTR_INTERNAL */
        if (stop != 0) {
            TRACE_INFO_STRING("Traverse handler returned STOP.", "");
            error = EINTR_INTERNAL;
        }
        /* Check what error we got */
        if (error == EINTR_INTERNAL) {
            TRACE_FLOW_NUMBER("Internal error - means we are stopping.", error);
            (*depth)--;
            return error;
        }
        else if (error) {
            TRACE_ERROR_NUMBER("Traverse handler returned error.", error);
            (*depth)--;
            return error;
        }

        parent = current;
        current = current->next;

    }

    TRACE_INFO_STRING("Out of loop", "");

    /* Check if we need to have a special
     * call at the end of the collection.
     */
    if ((mode_flags & COL_TRAVERSE_END) != 0) {

        /* Do this dummy invocation only:
         * a) If we are flattening and on the root level
         * b) We are not flattening
         */
        if ((((mode_flags & COL_TRAVERSE_FLAT) != 0) && (*depth == 1)) ||
            ((mode_flags & COL_TRAVERSE_FLAT) == 0)) {

            TRACE_INFO_STRING("About to do the special end collection invocation of handler", "");
            error = traverse_handler(ci, parent, current,
                                     traverse_data, user_item_handler,
                                     custom_data, &stop);
        }
    }

    TRACE_FLOW_NUMBER("col_walk_items. Returns: ", error);
    (*depth)--;
    return error;
}


/* ACTION */

/* Find an item by property name and perform an action on it. */
/* No pattern matching supported in the first implementation. */
/* To refer to child properties use notatation like this: */
/* parent!child!subchild!subsubchild etc.  */
static int col_find_item_and_do(struct collection_item *ci,
                                const char *property_to_find,
                                int type,
                                int mode_flags,
                                col_item_fn item_handler,
                                void *custom_data,
                                int action)
{

    int error = EOK;
    struct find_name *traverse_data = NULL;
    unsigned depth = 0;
    int count = 0;
    const char *last_part;
    char *sep;

    TRACE_FLOW_STRING("col_find_item_and_do", "Entry.");

    /* Item handler is always required */
    if ((item_handler == NULL) &&
        (action == COLLECTION_ACTION_FIND)) {
        TRACE_ERROR_NUMBER("No item handler - returning error!", EINVAL);
        return EINVAL;
    }

    /* Collection is requered */
    if (ci == NULL) {
        TRACE_ERROR_NUMBER("No collection to search!", EINVAL);
        return EINVAL;
    }

    /* Make sure that there is anything to search */
    type &= COL_TYPE_ANY;
    if (((property_to_find == NULL) && (type == 0)) ||
        ((*property_to_find == '\0') && (type == 0))) {
        TRACE_ERROR_NUMBER("No item search criteria specified - returning error!", ENOENT);
        return ENOENT;
    }
    /* Prepare data for traversal */
    traverse_data = (struct find_name *)malloc(sizeof(struct find_name));
    if (traverse_data == NULL) {
        TRACE_ERROR_NUMBER("Failed to allocate traverse data memory - returning error!", ENOMEM);
        return ENOMEM;
    }

    TRACE_INFO_STRING("col_find_item_and_do", "Filling in traverse data.");

    traverse_data->name_to_find = property_to_find;

    if (property_to_find != NULL) {

        traverse_data->name_len_to_find = strlen(property_to_find);

        /* Check if the search string ends with "!" - this is illegal */
        if (traverse_data->name_to_find[traverse_data->name_len_to_find - 1] == '!') {
            TRACE_ERROR_NUMBER("Search string is invalid.", EINVAL);
            free(traverse_data);
            return EINVAL;
        }

        /* Find last ! if any */
        sep = strrchr(traverse_data->name_to_find, '!');
        if (sep != NULL) {
            sep++;
            last_part = sep;
        }
        else last_part = traverse_data->name_to_find;

        TRACE_INFO_STRING("Last item", last_part);

        /* Create hash of the last part */
        traverse_data->hash = FNV1a_base;

        /* Create hash of the string to search */
        while(last_part[count] != 0) {
            traverse_data->hash = traverse_data->hash ^ toupper(last_part[count]);
            traverse_data->hash *= FNV1a_prime;
            count++;
        }
    }
    else {
        /* We a looking for a first element of a given type */
        TRACE_INFO_STRING("No search string", "");
        traverse_data->name_len_to_find = 0;
    }


    traverse_data->type_to_match = type;
    traverse_data->given_name = NULL;
    traverse_data->given_len = 0;
    traverse_data->current_path = NULL;
    traverse_data->action = action;

    mode_flags |= COL_TRAVERSE_END;

    TRACE_INFO_STRING("col_find_item_and_do", "About to walk the tree.");
    TRACE_INFO_NUMBER("Traverse flags", mode_flags);

    error = col_walk_items(ci, mode_flags, col_act_traverse_handler,
                           (void *)traverse_data, item_handler, custom_data,
                           &depth);

    if (traverse_data->current_path != NULL) {
        TRACE_INFO_STRING("find_item_and_do",
                          "Path was not cleared - deleting");
        col_delete_path_data(traverse_data->current_path);
    }

    free(traverse_data);

    if (error && (error != EINTR_INTERNAL)) {
        TRACE_ERROR_NUMBER("Walk items returned error. Returning: ", error);
        return error;
    }
    else {
        TRACE_FLOW_STRING("Walk items returned SUCCESS.", "");
        return EOK;
    }
}

/* Function to replace data in the item */
static int col_update_current_item(struct collection_item *current,
                                   struct update_property *update_data)
{
    TRACE_FLOW_STRING("col_update_current_item", "Entry");

    /* If type is different or same but it is string or binary we need to
     * replace the storage */
    if ((current->type != update_data->type) ||
        ((current->type == update_data->type) &&
        ((current->type == COL_TYPE_STRING) ||
         (current->type == COL_TYPE_BINARY)))) {
        TRACE_INFO_STRING("Replacing item data buffer", "");
        free(current->data);
        current->data = malloc(update_data->length);
        if (current->data == NULL) {
            TRACE_ERROR_STRING("Failed to allocate memory", "");
            current->length = 0;
            return ENOMEM;
        }
        current->length = update_data->length;
    }

    TRACE_INFO_STRING("Overwriting item data", "");
    memcpy(current->data, update_data->data, current->length);
    current->type = update_data->type;

    if (current->type == COL_TYPE_STRING)
        ((char *)(current->data))[current->length-1] = '\0';

    TRACE_FLOW_STRING("update_current_item", "Exit");
    return EOK;
}

/* TRAVERSE CALLBACKS */

/* Traverse handler for simple traverse function */
/* Handler must be able to deal with NULL current item */
static int col_simple_traverse_handler(struct collection_item *head,
                                       struct collection_item *previous,
                                       struct collection_item *current,
                                       void *traverse_data,
                                       col_item_fn user_item_handler,
                                       void *custom_data,
                                       int *stop)
{
    int error = EOK;
    struct collection_item end_item;
    char zero = '\0';

    TRACE_FLOW_STRING("col_simple_traverse_handler", "Entry.");

    if (current == NULL) {
        memset((void *)&end_item, 0, sizeof(struct collection_item));
        end_item.type = COL_TYPE_END;
        end_item.property = &zero;
        current = &end_item;
    }

    error = user_item_handler(current->property,
                              current->property_len,
                              current->type,
                              current->data,
                              current->length,
                              custom_data,
                              stop);

    TRACE_FLOW_NUMBER("col_simple_traverse_handler. Returning:", error);
    return error;
}

/* Traverse handler for to find parent */
static int col_parent_traverse_handler(struct collection_item *head,
                                       struct collection_item *previous,
                                       struct collection_item *current,
                                       void *traverse_data,
                                       col_item_fn user_item_handler,
                                       void *custom_data,
                                       int *stop)
{
    struct property_search *to_find;
    int done = 0;
    int match = 0;

    TRACE_FLOW_STRING("col_parent_traverse_handler", "Entry.");

    to_find = (struct property_search *)custom_data;

    TRACE_INFO_NUMBER("Looking for HASH:", (unsigned)(to_find->hash));
    TRACE_INFO_NUMBER("Current HASH:", (unsigned)(current->phash));

    /* Check hashes first */
    if(to_find->hash == current->phash) {

        /* Check type if we are asked to use type */
        if ((to_find->use_type) && (!(to_find->type & current->type))) {
            TRACE_FLOW_STRING("parent_traverse_handler. Returning:","Exit. Hash is Ok, type is not");
            return EOK;
        }

        /* Validate property. Make sure we include terminating 0 in the comparison */
        if (strncasecmp(current->property, to_find->property, current->property_len + 1) == 0) {

            match = 1;
            to_find->found = 1;

            /* Do the right thing based on index */
            /* If index is 0 we are looking for the first value in the list of duplicate properties */
            if (to_find->index == 0) done = 1;
            /* If index is non zero we are looking for N-th instance of the dup property */
            else if (to_find->index > 0) {
                if (to_find->count == to_find->index) done = 1;
                else {
                    /* Record found instance and move on */
                    to_find->parent = previous;
                    (to_find->count)++;
                }
            }
            /* If we are looking for last instance just record it */
            else to_find->parent = previous;
        }
    }

    if (done) {
        *stop = 1;
        *((struct collection_item **)traverse_data) = previous;
    }
    else {
        /* As soon as we found first non matching one but there was a match
         * return the parent of the last found item.
         */
        if (((!match) || (current->next == NULL)) && (to_find->index != 0) && (to_find->found)) {
            *stop = 1;
            if (to_find->index == -2)
                *((struct collection_item **)traverse_data) = to_find->parent;
            else
                *((struct collection_item **)traverse_data) = to_find->parent->next;
        }
    }


    TRACE_FLOW_STRING("col_parent_traverse_handler. Returning:","Exit");
    return EOK;
}


/* Traverse callback for find & delete function */
static int col_act_traverse_handler(struct collection_item *head,
                                    struct collection_item *previous,
                                    struct collection_item *current,
                                    void *passed_traverse_data,
                                    col_item_fn user_item_handler,
                                    void *custom_data,
                                    int *stop)
{
    int error = EOK;
    struct find_name *traverse_data = NULL;
    char *name;
    int length;
    struct path_data *temp;
    struct collection_header *header;
    char *property;
    int property_len;
    struct update_property *update_data;

    TRACE_FLOW_STRING("col_act_traverse_handler", "Entry.");

    traverse_data = (struct find_name *)passed_traverse_data;

    /* We can be called when current points to NULL */
    if (current == NULL) {
        TRACE_INFO_STRING("col_act_traverse_handler",
                          "Special call at the end of the collection.");
        temp = traverse_data->current_path;
        traverse_data->current_path = temp->previous_path;
        temp->previous_path = NULL;
        col_delete_path_data(temp);
        traverse_data->given_name = NULL;
        traverse_data->given_len = 0;
        TRACE_FLOW_NUMBER("Handling end of collection - removed path. Returning:", error);
        return error;
    }

    /* Create new path at the beginning of a new sub collection */
    if (current->type == COL_TYPE_COLLECTION) {

        TRACE_INFO_STRING("col_act_traverse_handler",
                          "Processing collection handle.");

        /* Create new path */
        if (traverse_data->current_path != NULL) {
            TRACE_INFO_STRING("Already have part of the path", "");
            name = traverse_data->current_path->name;
            length = traverse_data->current_path->length;
            TRACE_INFO_STRING("Path:", name);
            TRACE_INFO_NUMBER("Path len:", length);
        }
        else {
            name = NULL;
            length = 0;
        }

        if (traverse_data->given_name != NULL) {
            property = traverse_data->given_name;
            property_len = traverse_data->given_len;
        }
        else {
            property = current->property;
            property_len = current->property_len;
        }

        TRACE_INFO_STRING("col_act_traverse_handler", "About to create path data.");

        error = col_create_path_data(&(traverse_data->current_path),
                                     name, length,
                                     property, property_len, '!');

        TRACE_INFO_NUMBER("col_create_path_data returned:", error);
        return error;
    }

    /* Handle the collection pointers */
    if (current->type == COL_TYPE_COLLECTIONREF) {
        traverse_data->given_name = current->property;
        traverse_data->given_len = current->property_len;
        TRACE_INFO_STRING("Saved given name:", traverse_data->given_name);
    }

    TRACE_INFO_STRING("Processing item with property:", current->property);

    /* Do here what we do with items */
    if (col_match_item(current, traverse_data)) {
        TRACE_INFO_STRING("Matched item:", current->property);
        switch (traverse_data->action) {
        case COLLECTION_ACTION_FIND:
            TRACE_INFO_STRING("It is a find action - calling handler.", "");
            if (user_item_handler != NULL) {
                /* Call user handler */
                error = user_item_handler(current->property,
                                          current->property_len,
                                          current->type,
                                          current->data,
                                          current->length,
                                          custom_data,
                                          stop);

                TRACE_INFO_NUMBER("Handler returned:", error);
                TRACE_INFO_NUMBER("Handler set STOP to:", *stop);

            }
            break;

        case COLLECTION_ACTION_GET:
            TRACE_INFO_STRING("It is a get action.", "");
            if (custom_data != NULL)
                *((struct collection_item **)(custom_data)) = current;
            break;

        case COLLECTION_ACTION_DEL:
            TRACE_INFO_STRING("It is a delete action.", "");
            /* Make sure we tell the caller we found a match */
            if (custom_data != NULL)
                *(int *)custom_data = COL_MATCH;

            /* Adjust header of the collection */
            header = (struct collection_header *)head->data;
            header->count--;
            if (current->next == NULL)
                header->last = previous;

            /* Unlink and delete iteam */
            /* Previous can't be NULL here becuase we never delete
             * header elements */
            previous->next = current->next;
            col_delete_item(current);
            TRACE_INFO_STRING("Did the delete of the item.", "");
            break;

        case COLLECTION_ACTION_UPDATE:
            TRACE_INFO_STRING("It is an update action.", "");
            if((current->type == COL_TYPE_COLLECTION) ||
               (current->type == COL_TYPE_COLLECTIONREF)) {
                TRACE_ERROR_STRING("Can't update collections it is an error for now", "");
                return EINVAL;
            }

            /* Make sure we tell the caller we found a match */
            if (custom_data != NULL) {
                update_data = (struct update_property *)custom_data;
                update_data->found = COL_MATCH;
                error = col_update_current_item(current, update_data);
            }
            else {
                TRACE_ERROR_STRING("Error - update data is required", "");
                return EINVAL;
            }

            TRACE_INFO_STRING("Did the delete of the item.", "");
            break;
        default:
            break;
        }
        /* Force interrupt if we found */
        *stop = 1;
    }

    TRACE_FLOW_NUMBER("col_act_traverse_handler returning", error);
    return error;
}


/* Traverse handler for copy function */
static int col_copy_traverse_handler(struct collection_item *head,
                                     struct collection_item *previous,
                                     struct collection_item *current,
                                     void *passed_traverse_data,
                                     col_item_fn user_item_handler,
                                     void *custom_data,
                                     int *stop)
{
    int error = EOK;
    struct collection_item *parent;
    struct collection_item *other = NULL;
    struct col_copy *traverse_data;
    struct path_data *temp;
    char *name;
    int length;
    char *property = NULL;
    int property_len;
    struct collection_header *header;
    char *offset;

    TRACE_FLOW_STRING("col_copy_traverse_handler", "Entry.");

    parent = (struct collection_item *)custom_data;
    traverse_data = (struct col_copy *)passed_traverse_data;

    /* We can be called when current points to NULL */
    /* This will happen only in the FLATDOT case */
    if (current == NULL) {
        TRACE_INFO_STRING("col_copy_traverse_handler",
                          "Special call at the end of the collection.");
        temp = traverse_data->current_path;
        traverse_data->current_path = temp->previous_path;
        temp->previous_path = NULL;
        col_delete_path_data(temp);
        traverse_data->given_name = NULL;
        traverse_data->given_len = 0;
        TRACE_FLOW_NUMBER("Handling end of collection - removed path. Returning:", error);
        return error;
    }

    /* Create new path at the beginning of a new sub collection */
    if (current->type == COL_TYPE_COLLECTION) {

        TRACE_INFO_STRING("col_copy_traverse_handler",
                          "Processing collection handle.");
        if (traverse_data->mode == COL_COPY_FLATDOT) {
            /* Create new path */
            if (traverse_data->current_path != NULL) {
                TRACE_INFO_STRING("Already have part of the path", "");
                name = traverse_data->current_path->name;
                length = traverse_data->current_path->length;
                TRACE_INFO_STRING("Path:", name);
                TRACE_INFO_NUMBER("Path len:", length);
                if (traverse_data->given_name != NULL) {
                    property = traverse_data->given_name;
                    property_len = traverse_data->given_len;
                }
                else {
                    property = current->property;
                    property_len = current->property_len;
                }
            }
            else {
                /* Do not create prefix for top collection
                 * if there is no given name.
                 */
                name = NULL;
                length = 0;
                if (traverse_data->given_name != NULL) {
                    property = traverse_data->given_name;
                    property_len = traverse_data->given_len;
                }
                else {
                    property = NULL;
                    property_len = 0;
                }
            }

            TRACE_INFO_STRING("col_copy_traverse_handler", "About to create path data.");

            error = col_create_path_data(&(traverse_data->current_path),
                                         name, length,
                                         property, property_len, '.');

            TRACE_FLOW_NUMBER("col_copy_traverse_handler processed header:", error);
            return error;
        }
        else {
            TRACE_FLOW_NUMBER("col_copy_traverse_handler skipping the header:", error);
            return error;
        }
    }


    /* Check if this is a special case of sub collection */
    if (current->type == COL_TYPE_COLLECTIONREF) {

        TRACE_INFO_STRING("Found a subcollection we need to copy. Name:",
                          current->property);

        /* Based on the mode we need to do different things */
        switch (traverse_data->mode) {
        case COL_COPY_NORMAL:

            error = col_copy_collection(&other,
                                        *((struct collection_item **)(current->data)),
                                        current->property,
                                        COL_COPY_NORMAL);
            if (error) {
                TRACE_ERROR_NUMBER("Copy subcollection returned error:", error);
                return error;
            }

            /* Add new item to a collection
             * all references are now sub collections */
            error = col_insert_property_with_ref_int(parent,
                                                     NULL,
                                                     COL_DSP_END,
                                                     NULL,
                                                     0,
                                                     0,
                                                     current->property,
                                                     COL_TYPE_COLLECTIONREF,
                                                     (void *)(&other),
                                                     sizeof(struct collection_item **),
                                                     NULL);

            TRACE_FLOW_NUMBER("col_copy_traverse_handler returning in NORMAL mode:", error);
            return error;

       case COL_COPY_KEEPREF:

            /* Just increase reference count of the referenced collection */
			other = *((struct collection_item **)(current->data));
            header = (struct collection_header *)(other->data);
            header->reference_count++;

            /* Add new item to a collection
             * all references are now sub collections */
            error = col_insert_property_with_ref_int(parent,
                                                     NULL,
                                                     COL_DSP_END,
                                                     NULL,
                                                     0,
                                                     0,
                                                     current->property,
                                                     COL_TYPE_COLLECTIONREF,
                                                     (void *)(&other),
                                                     sizeof(struct collection_item **),
                                                     NULL);
            TRACE_FLOW_NUMBER("col_copy_traverse_handler returning in KEEPREF mode:", error);
            return error;

        case COL_COPY_TOP:
            /* Told to ignore sub collections */
            TRACE_FLOW_NUMBER("col_copy_traverse_handler returning in TOP mode:", error);
            return error;

        case COL_COPY_FLATDOT:

            traverse_data->given_name = current->property;
            traverse_data->given_len = current->property_len;
            TRACE_INFO_STRING("Saved given name:", traverse_data->given_name);
            TRACE_FLOW_NUMBER("col_copy_traverse_handler returning in FLATDOT mode:", error);
            return error;

        /* NOTE: The mode COL_COPY_FLAT is not in the list of cases becuase
         * in this flat mode we traverse collection using COL_TRAVERSE_FLAT flag
         * thus we should not be called on referenced collections at all
         * by the col_walk_items() function.
         */

        default:
            TRACE_ERROR_NUMBER("col_copy_traverse_handler bad mode error:", EINVAL);
            return EINVAL;
        }
    }
    else {

        if (traverse_data->mode == COL_COPY_FLATDOT) {
            /* Since this code can't use asprintf have to do it hard way */
            property = malloc(traverse_data->current_path->length +
                              current->property_len + 2);
            if (property == NULL) {
                TRACE_ERROR_NUMBER("Failed to allocate memory for a new name:", error);
                return error;
            }
            /* Add first part and dot only if we have prefix */
            offset = property;
            if (traverse_data->current_path->length) {
                memcpy(offset, traverse_data->current_path->name,
                       traverse_data->current_path->length);
                offset[traverse_data->current_path->length] = '.';
                offset += traverse_data->current_path->length + 1;
            }
            memcpy(offset, current->property, current->property_len);
            offset[current->property_len] = '\0';
        }
        else property = current->property;

        TRACE_INFO_STRING("Using property:", property);

        error = col_copy_item_with_cb(parent,
                                      property,
                                      current->type,
                                      current->data,
                                      current->length,
                                      traverse_data->copy_cb,
                                      traverse_data->ext_data);

        /* Free property if we allocated it */
        if (traverse_data->mode == COL_COPY_FLATDOT) free(property);

        if (error) {
            TRACE_ERROR_NUMBER("Failed to copy property:", error);
            return error;
        }
    }

    TRACE_FLOW_NUMBER("col_copy_traverse_handler returning", error);
    return error;
}




/********************* MAIN INTERFACE FUNCTIONS *****************************/


/* CREATE */

/* Function that creates an named collection of a given class*/
int col_create_collection(struct collection_item **ci, const char *name,
                          unsigned cclass)
{
    struct collection_item *handle = NULL;
    struct collection_header header;
    int error = EOK;

    TRACE_FLOW_STRING("col_create_collection", "Entry.");

    /* Prepare header */
    header.last = NULL;
    header.reference_count = 1;
    header.count = 0;
    header.cclass = cclass;

    /* Create a collection type property */
    error = col_insert_property_with_ref_int(NULL,
                                             NULL,
                                             COL_DSP_END,
                                             NULL,
                                             0,
                                             0,
                                             name,
                                             COL_TYPE_COLLECTION,
                                             &header,
                                             sizeof(header),
                                             &handle);


    if (error) return error;

    *ci = handle;

    TRACE_FLOW_STRING("col_create_collection", "Success Exit.");
    return EOK;
}


/* DESTROY */

/* Function that destroys a collection */
void col_destroy_collection(struct collection_item *ci)
{
    struct collection_header *header;

    TRACE_FLOW_STRING("col_destroy_collection", "Entry.");

    /* Do not try to delete NULL */
    if (ci == NULL) return;

    /* You can delete only whole collection not a part of it */
    if (ci->type != COL_TYPE_COLLECTION) {
        TRACE_ERROR_STRING("Attempt to delete a non collection - BAD!", "");
        TRACE_ERROR_NUMBER("Actual type is:", ci->type);
        return;
    }

    TRACE_INFO_STRING("Name:", ci->property);

    /* Collection can be referenced by other collection */
    header = (struct collection_header *)(ci->data);
    TRACE_INFO_NUMBER("Reference count:", header->reference_count);
    if (header->reference_count > 1) {
        TRACE_INFO_STRING("Dereferencing a referenced collection.", "");
        header->reference_count--;
        TRACE_INFO_NUMBER("Number after dereferencing.",
                          header->reference_count);
    }
    else {
        col_delete_collection(ci);
    }

    TRACE_FLOW_STRING("col_destroy_collection", "Exit.");
}


/* COPY */

/* Wrapper around a more advanced function */
int col_copy_collection(struct collection_item **collection_copy,
                        struct collection_item *collection_to_copy,
                        const char *name_to_use,
                        int copy_mode)
{
    int error = EOK;
    TRACE_FLOW_STRING("col_copy_collection", "Entry.");

    error = col_copy_collection_with_cb(collection_copy,
                                        collection_to_copy,
                                        name_to_use,
                                        copy_mode,
                                        NULL,
                                        NULL);

    TRACE_FLOW_NUMBER("col_copy_collection. Exit. Returning", error);
    return error;
}

/* Create a deep copy of the current collection. */
/* Referenced collections of the donor are copied as sub collections. */
int col_copy_collection_with_cb(struct collection_item **collection_copy,
                                struct collection_item *collection_to_copy,
                                const char *name_to_use,
                                int copy_mode,
                                col_copy_cb copy_cb,
                                void *ext_data)
{
    int error = EOK;
    struct collection_item *new_collection = NULL;
    const char *name;
    struct collection_header *header;
    unsigned depth = 0;
    struct col_copy traverse_data;
    int flags;

    TRACE_FLOW_STRING("col_copy_collection_with_cb", "Entry.");

    /* Collection is required */
    if (collection_to_copy == NULL) {
        TRACE_ERROR_NUMBER("No collection to search!", EINVAL);
        return EINVAL;
    }

    /* Storage is required too */
    if (collection_copy == NULL) {
        TRACE_ERROR_NUMBER("No memory provided to receive collection copy!", EINVAL);
        return EINVAL;
    }

    /* NOTE: Refine this check if adding a new copy mode */
    if ((copy_mode < 0) || (copy_mode > COL_COPY_TOP)) {
        TRACE_ERROR_NUMBER("Invalid copy mode:", copy_mode);
        return EINVAL;
    }

    /* Determine what name to use */
    if (name_to_use != NULL)
        name = name_to_use;
    else
        name = collection_to_copy->property;

    header = (struct collection_header *)collection_to_copy->data;

    /* Create a new collection */
    error = col_create_collection(&new_collection, name, header->cclass);
    if (error) {
        TRACE_ERROR_NUMBER("col_create_collection failed returning", error);
        return error;
    }

    traverse_data.mode = copy_mode;
    traverse_data.current_path = NULL;
    traverse_data.given_name = NULL;
    traverse_data.given_len = 0;
    traverse_data.copy_cb = copy_cb;
    traverse_data.ext_data = ext_data;

    if (copy_mode == COL_COPY_FLATDOT) flags = COL_TRAVERSE_DEFAULT | COL_TRAVERSE_END;
    else if (copy_mode == COL_COPY_FLAT) flags = COL_TRAVERSE_FLAT;
    else flags = COL_TRAVERSE_ONELEVEL;

    error = col_walk_items(collection_to_copy, flags,
                           col_copy_traverse_handler, (void *)(&traverse_data),
                           NULL, new_collection, &depth);

    if (!error) *collection_copy = new_collection;
    else col_destroy_collection(new_collection);

    TRACE_FLOW_NUMBER("col_copy_collection_with_cb returning", error);
    return error;

}


/* EXTRACTION */

/* Extract collection */
int col_get_collection_reference(struct collection_item *ci,
                                 struct collection_item **acceptor,
                                 const char *collection_to_find)
{
    struct collection_header *header;
    struct collection_item *subcollection = NULL;
    int error = EOK;

    TRACE_FLOW_STRING("col_get_collection_reference", "Entry.");

    if ((ci == NULL) ||
        (ci->type != COL_TYPE_COLLECTION) ||
        (acceptor == NULL)) {
        TRACE_ERROR_NUMBER("Invalid parameter - returning error",EINVAL);
        return EINVAL;
    }

    if (collection_to_find) {
        /* Find a sub collection */
        TRACE_INFO_STRING("We are given subcollection name - search it:",
                          collection_to_find);
        error = col_find_item_and_do(ci, collection_to_find,
                                     COL_TYPE_COLLECTIONREF,
                                     COL_TRAVERSE_DEFAULT,
                                     col_get_subcollection,
                                     (void *)(&subcollection),
                                     COLLECTION_ACTION_FIND);
        if (error) {
            TRACE_ERROR_NUMBER("Search failed returning error", error);
            return error;
        }

        if (subcollection == NULL) {
            TRACE_ERROR_STRING("Search for subcollection returned NULL pointer", "");
            return ENOENT;
        }
    }
    else {
        /* Create reference to the same collection */
        TRACE_INFO_STRING("Creating reference to the top level collection.", "");
        subcollection = ci;
    }

    header = (struct collection_header *)subcollection->data;
    TRACE_INFO_NUMBER("Count:", header->count);
    TRACE_INFO_NUMBER("Ref count:", header->reference_count);
    header->reference_count++;
    TRACE_INFO_NUMBER("Ref count after increment:", header->reference_count);
    *acceptor = subcollection;

    TRACE_FLOW_STRING("col_get_collection_reference", "Success Exit.");
    return EOK;
}

/* Get collection - if current item is a reference get a real collection from it. */
int col_get_reference_from_item(struct collection_item *ci,
                                struct collection_item **acceptor)
{
    struct collection_header *header;
    struct collection_item *subcollection = NULL;

    TRACE_FLOW_STRING("get_reference_from_item", "Entry.");

    if ((ci == NULL) ||
        (ci->type != COL_TYPE_COLLECTIONREF) ||
        (acceptor == NULL)) {
        TRACE_ERROR_NUMBER("Invalid parameter - returning error",EINVAL);
        return EINVAL;
    }

    subcollection = *((struct collection_item **)ci->data);

    header = (struct collection_header *)subcollection->data;
    TRACE_INFO_NUMBER("Count:", header->count);
    TRACE_INFO_NUMBER("Ref count:", header->reference_count);
    header->reference_count++;
    TRACE_INFO_NUMBER("Ref count after increment:", header->reference_count);
    *acceptor = subcollection;

    TRACE_FLOW_STRING("col_get_reference_from_item", "Success Exit.");
    return EOK;
}

/* ADDITION */

/* Add collection to collection */
int col_add_collection_to_collection(struct collection_item *ci,
                                     const char *sub_collection_name,
                                     const char *as_property,
                                     struct collection_item *collection_to_add,
                                     int mode)
{
    struct collection_item *acceptor = NULL;
    const char *name_to_use;
    struct collection_header *header;
    struct collection_item *collection_copy;
    int error = EOK;
    struct col_copy traverse_data;
    unsigned depth = 0;


    TRACE_FLOW_STRING("col_add_collection_to_collection", "Entry.");

    if ((ci == NULL) ||
        (ci->type != COL_TYPE_COLLECTION) ||
        (collection_to_add == NULL) ||
        (collection_to_add->type != COL_TYPE_COLLECTION)) {
        /* Need to debug here */
        TRACE_ERROR_NUMBER("Missing parameter - returning error", EINVAL);
        return EINVAL;
    }

    if (sub_collection_name != NULL) {
        /* Find a sub collection */
        TRACE_INFO_STRING("We are given subcollection name - search it:",
                          sub_collection_name);
        error = col_find_item_and_do(ci, sub_collection_name,
                                     COL_TYPE_COLLECTIONREF,
                                     COL_TRAVERSE_DEFAULT,
                                     col_get_subcollection,
                                     (void *)(&acceptor),
                                     COLLECTION_ACTION_FIND);
        if (error) {
            TRACE_ERROR_NUMBER("Search failed returning error", error);
            return error;
        }

        if (acceptor == NULL) {
            TRACE_ERROR_STRING("Search for subcollection returned NULL pointer", "");
            return ENOENT;
        }

    }
    else {
        acceptor = ci;
    }

    if (as_property != NULL)
        name_to_use = as_property;
    else
        name_to_use = collection_to_add->property;


    TRACE_INFO_STRING("Going to use name:", name_to_use);


    switch (mode) {
    case COL_ADD_MODE_REFERENCE:
        TRACE_INFO_STRING("We are adding a reference.", "");
        TRACE_INFO_NUMBER("Type of the header element:",
                          collection_to_add->type);
        TRACE_INFO_STRING("Header name we are adding.",
                          collection_to_add->property);
        /* Create a pointer to external collection */
        /* For future thread safety: Transaction start -> */
        error = col_insert_property_with_ref_int(acceptor,
                                                 NULL,
                                                 COL_DSP_END,
                                                 NULL,
                                                 0,
                                                 0,
                                                 name_to_use,
                                                 COL_TYPE_COLLECTIONREF,
                                                 (void *)(&collection_to_add),
                                                 sizeof(struct collection_item **),
                                                 NULL);

        TRACE_INFO_NUMBER("Type of the header element after adding property:",
                          collection_to_add->type);
        TRACE_INFO_STRING("Header name we just added.",
                          collection_to_add->property);
        if (error) {
            TRACE_ERROR_NUMBER("Adding property failed with error:", error);
            return error;
        }
        header = (struct collection_header *)collection_to_add->data;
        TRACE_INFO_NUMBER("Count:", header->count);
        TRACE_INFO_NUMBER("Ref count:", header->reference_count);
        header->reference_count++;
        TRACE_INFO_NUMBER("Ref count after increment:",
                          header->reference_count);
        /* -> Transaction end */
        break;

    case COL_ADD_MODE_EMBED:
        TRACE_INFO_STRING("We are embedding the collection.", "");
        /* First check if the passed in collection is referenced more than once */
        TRACE_INFO_NUMBER("Type of the header element we are adding:",
                          collection_to_add->type);
        TRACE_INFO_STRING("Header name we are adding.",
                          collection_to_add->property);
        TRACE_INFO_NUMBER("Type of the header element we are adding to:",
                          acceptor->type);
        TRACE_INFO_STRING("Header name we are adding to.",
                          acceptor->property);

        error = col_insert_property_with_ref_int(acceptor,
                                                 NULL,
                                                 COL_DSP_END,
                                                 NULL,
                                                 0,
                                                 0,
                                                 name_to_use,
                                                 COL_TYPE_COLLECTIONREF,
                                                 (void *)(&collection_to_add),
                                                 sizeof(struct collection_item **),
                                                 NULL);


        TRACE_INFO_NUMBER("Adding property returned:", error);
        break;

    case COL_ADD_MODE_CLONE:
        TRACE_INFO_STRING("We are cloning the collection.", "");
        TRACE_INFO_STRING("Name we will use.", name_to_use);

        /* For future thread safety: Transaction start -> */
        error = col_copy_collection(&collection_copy,
                                    collection_to_add, name_to_use,
                                    COL_COPY_NORMAL);
        if (error) return error;

        TRACE_INFO_STRING("We have a collection copy.", collection_copy->property);
        TRACE_INFO_NUMBER("Collection type.", collection_copy->type);
        TRACE_INFO_STRING("Acceptor collection.", acceptor->property);
        TRACE_INFO_NUMBER("Acceptor collection type.", acceptor->type);

        error = col_insert_property_with_ref_int(acceptor,
                                                 NULL,
                                                 COL_DSP_END,
                                                 NULL,
                                                 0,
                                                 0,
                                                 name_to_use,
                                                 COL_TYPE_COLLECTIONREF,
                                                 (void *)(&collection_copy),
                                                 sizeof(struct collection_item **),
                                                 NULL);

        /* -> Transaction end */
        TRACE_INFO_NUMBER("Adding property returned:", error);
        break;

    case COL_ADD_MODE_FLAT:
        TRACE_INFO_STRING("We are flattening the collection.", "");

        traverse_data.mode = COL_COPY_FLAT;
        traverse_data.current_path = NULL;
        traverse_data.copy_cb = NULL;
        traverse_data.ext_data = NULL;

        if ((as_property) && (*as_property)) {
            /* The normal assignement generates a warning
             * becuase I am assigning const to a non const.
             * I can't make the structure member to be const
             * since it changes but it changes
             * to point to different stings at different time
             * This is just an initial sting it will use.
             * The logic does not change the content of the string.
             * To overcome the issue I use memcpy();
             */
            memcpy(&(traverse_data.given_name),
                   &(as_property), sizeof(char *));
            traverse_data.given_len = strlen(as_property);
        }
        else {
            traverse_data.given_name = NULL;
            traverse_data.given_len = 0;
        }

        error = col_walk_items(collection_to_add, COL_TRAVERSE_FLAT,
                               col_copy_traverse_handler, (void *)(&traverse_data),
                               NULL, acceptor, &depth);

        TRACE_INFO_NUMBER("Copy collection flat returned:", error);
        break;

    case COL_ADD_MODE_FLATDOT:
        TRACE_INFO_STRING("We are flattening the collection with dots.", "");

        traverse_data.mode = COL_COPY_FLATDOT;
        traverse_data.current_path = NULL;
        traverse_data.copy_cb = NULL;
        traverse_data.ext_data = NULL;

        if ((as_property) && (*as_property)) {
            /* The normal assignement generates a warning
             * becuase I am assigning const to a non const.
             * I can't make the structure member to be const
             * since it changes but it changes
             * to point to different stings at different time
             * This is just an initial sting it will use.
             * The logic does not change the content of the string.
             * To overcome the issue I use memcpy();
             */
            memcpy(&(traverse_data.given_name),
                   &(as_property), sizeof(char *));
            traverse_data.given_len = strlen(as_property);
        }
        else {
            traverse_data.given_name = NULL;
            traverse_data.given_len = 0;
        }

        error = col_walk_items(collection_to_add, COL_TRAVERSE_DEFAULT | COL_TRAVERSE_END,
                               col_copy_traverse_handler, (void *)(&traverse_data),
                               NULL, acceptor, &depth);

        TRACE_INFO_NUMBER("Copy collection flatdot returned:", error);
        break;

    default:
        error = EINVAL;
    }

    TRACE_FLOW_NUMBER("col_add_collection_to_collection returning:", error);
    return error;
}

/* TRAVERSING */

/* Function to traverse the entire collection including optionally
 * sub collections */
int col_traverse_collection(struct collection_item *ci,
                            int mode_flags,
                            col_item_fn item_handler,
                            void *custom_data)
{

    int error = EOK;
    unsigned depth = 0;

    TRACE_FLOW_STRING("col_traverse_collection", "Entry.");

    if (ci == NULL) {
        TRACE_ERROR_NUMBER("No collection to traverse!", EINVAL);
        return EINVAL;
    }

    error = col_walk_items(ci, mode_flags, col_simple_traverse_handler,
                           NULL, item_handler, custom_data, &depth);

    if ((error != 0) && (error != EINTR_INTERNAL)) {
        TRACE_ERROR_NUMBER("Error walking tree", error);
        return error;
    }

    TRACE_FLOW_STRING("col_traverse_collection", "Success exit.");
    return EOK;
}

/* CHECK */

/* Convenience function to check if specific property is in the collection */
int col_is_item_in_collection(struct collection_item *ci,
                              const char *property_to_find,
                              int type,
                              int mode_flags,
                              int *found)
{
    int error;

    TRACE_FLOW_STRING("col_is_item_in_collection","Entry.");

    *found = COL_NOMATCH;
    error = col_find_item_and_do(ci, property_to_find,
                                 type, mode_flags,
                                 col_is_in_item_handler,
                                 (void *)found,
                                 COLLECTION_ACTION_FIND);

    TRACE_FLOW_NUMBER("col_is_item_in_collection returning", error);
    return error;
}

/* SEARCH */
/* Search function. Looks up an item in the collection based on the property.
   Essentually it is a traverse function with spacial traversing logic.
 */
int col_get_item_and_do(struct collection_item *ci,
                        const char *property_to_find,
                        int type,
                        int mode_flags,
                        col_item_fn item_handler,
                        void *custom_data)
{
    int error = EOK;

    TRACE_FLOW_STRING("col_get_item_and_do","Entry.");

    error = col_find_item_and_do(ci, property_to_find,
                                 type, mode_flags,
                                 item_handler,
                                 custom_data,
                                 COLLECTION_ACTION_FIND);

    TRACE_FLOW_NUMBER("col_get_item_and_do returning", error);
    return error;
}


/* Get raw item */
int col_get_item(struct collection_item *ci,
                 const char *property_to_find,
                 int type,
                 int mode_flags,
                 struct collection_item **item)
{

    int error = EOK;

    TRACE_FLOW_STRING("col_get_item", "Entry.");

    error = col_find_item_and_do(ci, property_to_find,
                                 type, mode_flags,
                                 NULL, (void *)item,
                                 COLLECTION_ACTION_GET);

    TRACE_FLOW_NUMBER("col_get_item returning", error);
    return error;
}

/* DELETE */
/* Delete property from the collection */
int col_delete_property(struct collection_item *ci,
                        const char *property_to_find,
                        int type,
                        int mode_flags)
{
    int error = EOK;
    int found;

    TRACE_FLOW_STRING("col_delete_property", "Entry.");
    found = COL_NOMATCH;

    error = col_find_item_and_do(ci, property_to_find,
                                 type, mode_flags,
                                 NULL, (void *)(&found),
                                 COLLECTION_ACTION_DEL);

    if ((error == EOK) && (found == COL_NOMATCH))
        error = ENOENT;

    TRACE_FLOW_NUMBER("col_delete_property returning", error);
    return error;
}

/* UPDATE */
/* Update property in the collection */
int col_update_property(struct collection_item *ci,
                        const char *property_to_find,
                        int type,
                        void *new_data,
                        int length,
                        int mode_flags)
{
    int error = EOK;
    struct update_property update_data;

    TRACE_FLOW_STRING("col_update_property", "Entry.");
    update_data.type = type;
    update_data.data = new_data;
    update_data.length = length;
    update_data.found = COL_NOMATCH;

    error = col_find_item_and_do(ci, property_to_find,
                                 type, mode_flags,
                                 NULL, (void *)(&update_data),
                                 COLLECTION_ACTION_UPDATE);

    if ((error == EOK) && (update_data.found == COL_NOMATCH))
        error = ENOENT;

    TRACE_FLOW_NUMBER("col_update_property returning", error);
    return error;
}


/* Function to modify the item */
int col_modify_item(struct collection_item *item,
                    const char *property,
                    int type,
                    const void *data,
                    int length)
{
    TRACE_FLOW_STRING("col_modify_item", "Entry");

    if ((item == NULL) ||
        (item->type == COL_TYPE_COLLECTION) ||
        (item->type == COL_TYPE_COLLECTIONREF)) {
        TRACE_ERROR_NUMBER("Invalid argument or invalid argument type", EINVAL);
        return EINVAL;
    }

    if (property != NULL) {
        if (col_validate_property(property)) {
            TRACE_ERROR_STRING("Invalid chracters in the property name", property);
            return EINVAL;
        }
        free(item->property);
        item->property = strdup(property);
        if (item->property == NULL) {
            TRACE_ERROR_STRING("Failed to allocate memory", "");
            return ENOMEM;
        }

        /* Update property length and hash if we rename the property */
        item->phash = col_make_hash(property, 0, &(item->property_len));
        TRACE_INFO_NUMBER("Item hash", item->phash);
        TRACE_INFO_NUMBER("Item property length", item->property_len);
        TRACE_INFO_NUMBER("Item property strlen", strlen(item->property));

    }

    /* We need to change data ? */
    if(length) {

        /* If type is different or same but it is string or binary we need to
         * replace the storage */
        if ((item->type != type) ||
            ((item->type == type) &&
            ((item->type == COL_TYPE_STRING) || (item->type == COL_TYPE_BINARY)))) {
            TRACE_INFO_STRING("Replacing item data buffer", "");
            free(item->data);
            item->data = malloc(length);
            if (item->data == NULL) {
                TRACE_ERROR_STRING("Failed to allocate memory", "");
                item->length = 0;
                return ENOMEM;
            }
            item->length = length;
        }

        TRACE_INFO_STRING("Overwriting item data", "");
        memcpy(item->data, data, item->length);
        item->type = type;

        if (item->type == COL_TYPE_STRING)
            ((char *)(item->data))[item->length - 1] = '\0';
    }

    TRACE_FLOW_STRING("col_modify_item", "Exit");
    return EOK;
}


/* Set collection class */
int col_set_collection_class(struct collection_item *item,
                             unsigned cclass)
{
    struct collection_header *header;

    TRACE_FLOW_STRING("col_set_collection_class", "Entry");

    if (item->type != COL_TYPE_COLLECTION) {
        TRACE_INFO_NUMBER("Not a collectin object. Type is", item->type);
        return EINVAL;
    }

    header = (struct collection_header *)item->data;
    header->cclass = cclass;
    TRACE_FLOW_STRING("col_set_collection_class", "Exit");
    return EOK;
}

/* Get collection class */
int col_get_collection_class(struct collection_item *item,
                             unsigned *cclass)
{
    struct collection_header *header;

    TRACE_FLOW_STRING("col_get_collection_class", "Entry");

    if (item->type != COL_TYPE_COLLECTION) {
        TRACE_ERROR_NUMBER("Not a collection object. Type is", item->type);
        return EINVAL;
    }

    header = (struct collection_header *)item->data;
    *cclass  = header->cclass;
    TRACE_FLOW_STRING("col_get_collection_class", "Exit");
    return EOK;
}

/* Get collection count */
int col_get_collection_count(struct collection_item *item,
                             unsigned *count)
{
    struct collection_header *header;

    TRACE_FLOW_STRING("col_get_collection_count", "Entry");

    if (item->type != COL_TYPE_COLLECTION) {
        TRACE_ERROR_NUMBER("Not a collectin object. Type is", item->type);
        return EINVAL;
    }

    header = (struct collection_header *)item->data;
    *count  = header->count;
    TRACE_FLOW_STRING("col_get_collection_count", "Exit");
    return EOK;

}

/* Convinience function to check if the collection is of the specific class */
/* In case of internal error assumes that collection is not of the right class */
int col_is_of_class(struct collection_item *item, unsigned cclass)
{
    int error = EOK;
    unsigned ret_class = 0;

    TRACE_FLOW_STRING("col_is_of_class invoked", "");

    error = col_get_collection_class(item, &ret_class);
    if (error || (ret_class != cclass))
        return 0;
    else
        return 1;
}

/* Get propery */
const char *col_get_item_property(struct collection_item *ci,
                                  int *property_len)
{
    if (property_len != NULL) *property_len = ci->property_len;
    return ci->property;
}

/* Get type */
int col_get_item_type(struct collection_item *ci)
{
    return ci->type;
}

/* Get length */
int col_get_item_length(struct collection_item *ci)
{
    return ci->length;
}

/* Get data */
void *col_get_item_data(struct collection_item *ci)
{
    return ci->data;
}

/* Get hash */
uint64_t col_get_item_hash(struct collection_item *ci)
{
    return ci->phash;
}

/* Calculates hash of the string using internal hashing
 * algorithm. Populates "length" with length
 * of the string not counting 0.
 * Length argument can be NULL.
 */
uint64_t col_make_hash(const char *string, int sub_len, int *length)
{
    uint64_t hash = 0;
    int str_len = 0;

    TRACE_FLOW_STRING("col_make_hash called for string:", string);

    if (string) {
        hash = FNV1a_base;
        while (string[str_len] != 0) {

            /* Check if we need to stop */
            if ((sub_len > 0) && (str_len == sub_len)) break;

            hash = hash ^ toupper(string[str_len]);
            hash *= FNV1a_prime;
            str_len++;
        }
    }

    if (length) *length = str_len;

    TRACE_FLOW_NUMBER("col_make_hash returning hash:", hash);

    return hash;
}
