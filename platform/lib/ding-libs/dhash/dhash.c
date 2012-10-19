/*
    Authors:
        John Dennis <jdennis.redhat.com>
        Esmond Pitt <ejp@ausmelb.oz.AU>

    This implementation was based on a 3/7/1989 public domain submission
    to comp.sources.misc by Esmond Pitt <ejp@ausmelb.oz.AU>.

    Copyright (C) 2009 Red Hat

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU Lesser General Public License as published by
    the Free Software Foundation; either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Lesser General Public License for more details.

    You should have received a copy of the GNU Lesser General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/

/*****************************************************************************/
/******************************** Documentation ******************************/
/*****************************************************************************/

/*
 * See documentation in corresponding header file dhash.h.
 *
 * Compilation controls:
 * DEBUG controls some informative traces, mainly for debugging.
 * HASH_STATISTICS causes hash_accesses and hash_collisions to be maintained;
 * when combined with DEBUG, these are displayed by hash_destroy().
 *
 */

/*****************************************************************************/
/******************************* Include Files *******************************/
/*****************************************************************************/

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <errno.h>
#include "dhash.h"

/*****************************************************************************/
/****************************** Internal Defines *****************************/
/*****************************************************************************/

#define PRIME_1                 37
#define PRIME_2                 1048583

#ifndef MIN
    #define MIN(a,b) (((a) < (b)) ? (a) : (b))
#endif

#ifndef MAX
    #define MAX(a,b) (((a) > (b)) ? (a) : (b))
#endif

#define halloc(table, size) table->halloc(size, table->halloc_pvt)
#define hfree(table, ptr) table->hfree(ptr, table->halloc_pvt)
#define hdelete_callback(table, type, entry) do { \
    if (table->delete_callback) { \
        table->delete_callback(entry, type, table->delete_pvt); \
    } \
} while(0)

/*****************************************************************************/
/************************** Internal Type Definitions ************************/
/*****************************************************************************/

typedef struct element_t {
    hash_entry_t entry;
    struct element_t *next;
} element_t, *segment_t;


struct hash_table_str {
    unsigned long   p;             /* Next bucket to be split */
    unsigned long   maxp;          /* upper bound on p during expansion */
    unsigned long   entry_count;   /* current # entries */
    unsigned long   bucket_count;  /* current # buckets */
    unsigned long   segment_count; /* current # segments */
    unsigned long   min_load_factor;
    unsigned long   max_load_factor;
    unsigned long   directory_size;
    unsigned int    directory_size_shift;
    unsigned long   segment_size;
    unsigned int    segment_size_shift;
    hash_delete_callback *delete_callback;
    void *delete_pvt;
    hash_alloc_func *halloc;
    hash_free_func *hfree;
    void *halloc_pvt;
    segment_t **directory;
#ifdef HASH_STATISTICS
    hash_statistics_t statistics;
#endif

};

typedef unsigned long address_t;

typedef struct hash_keys_callback_data_t {
    unsigned long index;
    hash_key_t *keys;
} hash_keys_callback_data_t;

typedef struct hash_values_callback_data_t {
    unsigned long index;
    hash_value_t *values;
} hash_values_callback_data_t;

struct _hash_iter_context_t {
    struct hash_iter_context_t iter;
    hash_table_t *table;
    unsigned long i, j;
    segment_t *s;
    element_t *p;
};

/*****************************************************************************/
/**********************  External Function Declarations  *********************/
/*****************************************************************************/

/*****************************************************************************/
/**********************  Internal Function Declarations  *********************/
/*****************************************************************************/

static address_t convert_key(hash_key_t *key);
static address_t hash(hash_table_t *table, hash_key_t *key);
static bool key_equal(hash_key_t *a, hash_key_t *b);
static int contract_table(hash_table_t *table);
static int expand_table(hash_table_t *table);
static hash_entry_t *hash_iter_next(struct hash_iter_context_t *iter);

/*****************************************************************************/
/*************************  External Global Variables  ***********************/
/*****************************************************************************/

/*****************************************************************************/
/*************************  Internal Global Variables  ***********************/
/*****************************************************************************/

#if DEBUG
int debug_level = 1;
#endif

/*****************************************************************************/
/***************************  Internal Functions  ****************************/
/*****************************************************************************/

static void *sys_malloc_wrapper(size_t size, void *pvt)
{
    return malloc(size);
}

static void sys_free_wrapper(void *ptr, void *pvt)
{
    return free(ptr);
}

static address_t convert_key(hash_key_t *key)
{
    address_t h;
    unsigned char *k;

    switch(key->type) {
    case HASH_KEY_ULONG:
        h = key->ul;
        break;
    case HASH_KEY_STRING:
        /* Convert string to integer */
        for (h = 0, k = (unsigned char *) key->str; *k; k++)
            h = h * PRIME_1 ^ (*k - ' ');
        break;
    default:
        h = key->ul;
        break;
    }
    return h;
}

static address_t hash(hash_table_t *table, hash_key_t *key)
{
    address_t h, address;

    h = convert_key(key);
    h %= PRIME_2;
    address = h & (table->maxp-1);            /* h % maxp */
    if (address < table->p)
        address = h & ((table->maxp << 1)-1); /* h % (2*table->maxp) */

    return address;
}

static bool is_valid_key_type(hash_key_enum key_type)
{
    switch(key_type) {
    case HASH_KEY_ULONG:
    case HASH_KEY_STRING:
        return true;
    default:
        return false;
    }
}

static bool is_valid_value_type(hash_value_enum value_type)
{
    switch(value_type) {
    case HASH_VALUE_UNDEF:
    case HASH_VALUE_PTR:
    case HASH_VALUE_INT:
    case HASH_VALUE_UINT:
    case HASH_VALUE_LONG:
    case HASH_VALUE_ULONG:
    case HASH_VALUE_FLOAT:
    case HASH_VALUE_DOUBLE:
        return true;
    default:
        return false;
    }
}

static bool key_equal(hash_key_t *a, hash_key_t *b)
{
    if (a->type != b->type) return false;

    switch(a->type) {
    case HASH_KEY_ULONG:
        return (a->ul == b->ul);
    case HASH_KEY_STRING:
        return (strcmp(a->str, b->str) == 0);
    }
    return false;
}


static int expand_table(hash_table_t *table)
{
    address_t  new_address;
    unsigned long old_segment_index, new_segment_index;
    unsigned long old_segment_dir, new_segment_dir;
    segment_t *old_segment, *new_segment;
    element_t *current, **previous, **last_of_new;

    if (table->bucket_count < (table->directory_size << table->segment_size_shift)) {
#ifdef DEBUG
        if (debug_level >= 2)
            fprintf(stderr, "expand_table on entry: bucket_count=%lu, segment_count=%lu p=%lu maxp=%lu\n",
                    table->bucket_count, table->segment_count, table->p, table->maxp);
#endif
#ifdef HASH_STATISTICS
        table->statistics.table_expansions++;
#endif

        /*
         * Locate the bucket to be split
         */
        old_segment_dir = table->p >> table->segment_size_shift;
        old_segment = table->directory[old_segment_dir];
        old_segment_index = table->p & (table->segment_size-1); /* p % segment_size */
        /*
         * Expand address space; if necessary create a new segment
         */
        new_address = table->maxp + table->p;
        new_segment_dir = new_address >> table->segment_size_shift;
        new_segment_index = new_address & (table->segment_size-1); /* new_address % segment_size */
        if (new_segment_index == 0) {
            table->directory[new_segment_dir] = (segment_t *)halloc(table, table->segment_size * sizeof(segment_t));
            if (table->directory[new_segment_dir] == NULL) {
                return HASH_ERROR_NO_MEMORY;
            }
            memset(table->directory[new_segment_dir], 0, table->segment_size * sizeof(segment_t));
            table->segment_count++;
        }
        new_segment = table->directory[new_segment_dir];
        /*
         * Adjust state variables
         */
        table->p++;
        if (table->p == table->maxp) {
            table->maxp <<= 1;  /* table->maxp *= 2 */
            table->p = 0;
        }
        table->bucket_count++;
        /*
         * Relocate records to the new bucket
         */
        previous = &old_segment[old_segment_index];
        current = *previous;
        last_of_new = &new_segment[new_segment_index];
        *last_of_new = NULL;
        while (current != NULL) {
            if (hash(table, &current->entry.key) == new_address) {
                /*
                 * Attach it to the end of the new chain
                 */
                *last_of_new = current;
                /*
                 * Remove it from old chain
                 */
                *previous = current->next;
                last_of_new = &current->next;
                current = current->next;
                *last_of_new = NULL;
            } else {
                /*
                 * leave it on the old chain
                 */
                previous = &current->next;
                current = current->next;
            }
        }
#ifdef DEBUG
        if (debug_level >= 2)
            fprintf(stderr, "expand_table on exit: bucket_count=%lu, segment_count=%lu p=%lu maxp=%lu\n",
                    table->bucket_count, table->segment_count, table->p, table->maxp);
#endif
    }
    return HASH_SUCCESS;
}

static int contract_table(hash_table_t *table)
{
    address_t  new_address, old_address;
    unsigned long old_segment_index, new_segment_index;
    unsigned long old_segment_dir, new_segment_dir;
    segment_t *old_segment, *new_segment;
    element_t *current;

    if ((table->bucket_count > table->segment_size) && (table->segment_count > 1)) {
#ifdef DEBUG
        if (debug_level >= 2)
            fprintf(stderr, "contract_table on entry: bucket_count=%lu, segment_count=%lu p=%lu maxp=%lu\n",
                    table->bucket_count, table->segment_count, table->p, table->maxp);
#endif

#ifdef HASH_STATISTICS
        table->statistics.table_contractions++;
#endif
        /*
         * Locate the bucket to be merged with the last bucket
         */
        old_address = table->bucket_count - 1;
        old_segment_dir = old_address >> table->segment_size_shift;
        old_segment = table->directory[old_segment_dir];
        old_segment_index = old_address & (table->segment_size-1); /* old_address % segment_size */

        /*
         * Adjust state variables
         */
        if (table->p > 0) {
            table->p--;
        } else {
            table->maxp >>= 1;
            table->p = table->maxp - 1;
        }
        table->bucket_count--;

        /*
         * Find the last bucket to merge back
         */
        if((current = old_segment[old_segment_index]) != NULL) {
            new_address = hash(table, &old_segment[old_segment_index]->entry.key);
            new_segment_dir = new_address >> table->segment_size_shift;
            new_segment_index = new_address & (table->segment_size-1); /* new_address % segment_size */
            new_segment = table->directory[new_segment_dir];

            /*
             * Relocate records to the new bucket by splicing the two chains
             * together by inserting the old chain at the head of the new chain.
             * First find the end of the old chain, then set its next pointer to
             * point to the head of the new chain, set the head of the new chain to
             * point to the old chain, then finally set the head of the old chain to
             * NULL.
             */

            while (current->next != NULL) {
                current = current->next;
            }

            current->next = new_segment[new_segment_index];
            new_segment[new_segment_index] = old_segment[old_segment_index];
            old_segment[old_segment_index] = NULL;
        }
        /*
         * If we have removed the last of the chains in this segment then free the
         * segment since its no longer in use.
         */
        if (old_segment_index == 0) {
            table->segment_count--;
            hfree(table, table->directory[old_segment_dir]);
        }

#ifdef DEBUG
        if (debug_level >= 2)
            fprintf(stderr, "contract_table on exit: bucket_count=%lu, segment_count=%lu p=%lu maxp=%lu\n",
                    table->bucket_count, table->segment_count, table->p, table->maxp);
#endif

    }
    return HASH_SUCCESS;
}

static int lookup(hash_table_t *table, hash_key_t *key, element_t **element_arg, segment_t **chain_arg)
{
    address_t h;
    segment_t *current_segment;
    unsigned long segment_index, segment_dir;
    segment_t *chain, element;

    *element_arg = NULL;
    *chain_arg = NULL;

    if (!table) return HASH_ERROR_BAD_TABLE;

#ifdef HASH_STATISTICS
    table->statistics.hash_accesses++;
#endif
    h = hash(table, key);
    segment_dir = h >> table->segment_size_shift;
    segment_index = h & (table->segment_size-1); /* h % segment_size */
    /*
     * valid segment ensured by hash()
     */
    current_segment = table->directory[segment_dir];

#ifdef DEBUG
    if (debug_level >= 3)
        fprintf(stderr, "lookup: h=%lu, segment_dir=%lu, segment_index=%lu current_segment=%p\n",
                h, segment_dir, segment_index, current_segment);
#endif

    if (current_segment == NULL) return EFAULT;
    chain = &current_segment[segment_index];
    element = *chain;
    /*
     * Follow collision chain
     */
    while (element != NULL && !key_equal(&element->entry.key, key)) {
        chain = &element->next;
        element = *chain;
#ifdef HASH_STATISTICS
        table->statistics.hash_collisions++;
#endif
    }
    *element_arg = element;
    *chain_arg = chain;

    return HASH_SUCCESS;
}

static bool hash_keys_callback(hash_entry_t *item, void *user_data)
{
    hash_keys_callback_data_t *data = (hash_keys_callback_data_t *)user_data;

    data->keys[data->index++] = item->key;
    return true;
}

static bool hash_values_callback(hash_entry_t *item, void *user_data)
{
    hash_values_callback_data_t *data = (hash_values_callback_data_t *)user_data;

    data->values[data->index++] = item->value;
    return true;
}

/*****************************************************************************/
/****************************  Exported Functions  ***************************/
/*****************************************************************************/

const char* hash_error_string(int error)
{
    switch(error) {
    case HASH_SUCCESS:              return "Success";
    case HASH_ERROR_BAD_KEY_TYPE:   return "Bad key type";
    case HASH_ERROR_BAD_VALUE_TYPE: return "Bad value type";
    case HASH_ERROR_NO_MEMORY:      return "No memory";
    case HASH_ERROR_KEY_NOT_FOUND:  return "Key not found";
    case HASH_ERROR_BAD_TABLE:      return "Bad table";
    }
    return NULL;
}


int hash_create(unsigned long count, hash_table_t **tbl,
                hash_delete_callback *delete_callback,
                void *delete_private_data)
{
    return hash_create_ex(count, tbl, 0, 0, 0, 0,
                          NULL, NULL, NULL,
                          delete_callback,
                          delete_private_data);
}

int hash_create_ex(unsigned long count, hash_table_t **tbl,
                   unsigned int directory_bits,
                   unsigned int segment_bits,
                   unsigned long min_load_factor,
                   unsigned long max_load_factor,
                   hash_alloc_func *alloc_func,
                   hash_free_func *free_func,
                   void *alloc_private_data,
                   hash_delete_callback *delete_callback,
                   void *delete_private_data) {
    unsigned long i;
    unsigned int n_addr_bits, requested_bits;
    unsigned int requested_directory_bits;
    unsigned int requested_segment_bits;
    address_t addr;
    hash_table_t *table = NULL;

    /* Initialize to NULL in case of an early return due to an error */
    *tbl = NULL;

    if (alloc_func == NULL) alloc_func = sys_malloc_wrapper;
    if (free_func == NULL) free_func = sys_free_wrapper;

    /* Compute directory and segment parameters */

    /* compute power of 2 >= count; it's the number of requested buckets */
    if (count > 1) {
        for (requested_bits = 0; (1 << requested_bits) < count; requested_bits++);
    } else {
        requested_bits = 1;
    }

    /*
     * If caller didn't specify directory & segment allocation then
     * compute it from the requested count.
     */
    if (directory_bits == 0 || segment_bits == 0) {
        /* Equally divide buckets between the directory and segments */
        requested_directory_bits = MAX(requested_bits >> 1, 1);
        requested_segment_bits = MAX(requested_bits - requested_directory_bits, 1);

        /* If the requested count wasn't specified pick a default */
        if (count == 0) {
            directory_bits = MAX(requested_directory_bits, HASH_DEFAULT_DIRECTORY_BITS);
            segment_bits = MAX(requested_segment_bits, HASH_DEFAULT_SEGMENT_BITS);
        } else {
            directory_bits = requested_directory_bits;
            segment_bits = requested_segment_bits;
        }
    }

    for (addr = ~0, n_addr_bits = 0; addr; addr >>= 1, n_addr_bits++);

    if (directory_bits + segment_bits > n_addr_bits) return EINVAL;

    table = (hash_table_t *)alloc_func(sizeof(hash_table_t),
                                       alloc_private_data);
    if (table == NULL) {
        return HASH_ERROR_NO_MEMORY;
    }
    memset(table, 0, sizeof(hash_table_t));
    table->halloc = alloc_func;
    table->hfree = free_func;
    table->halloc_pvt = alloc_private_data;

    table->directory_size_shift = directory_bits;
    table->directory_size = directory_bits ? 1 << directory_bits : 0;

    table->segment_size_shift = segment_bits;
    table->segment_size = segment_bits ? 1 << segment_bits : 0;

    /* Allocate directory */
    table->directory = (segment_t **)halloc(table, table->directory_size * sizeof(segment_t *));
    if (table->directory == NULL) {
        hash_destroy(table);
        return HASH_ERROR_NO_MEMORY;
    }
    memset(table->directory, 0, table->directory_size * sizeof(segment_t *));

    /*
     * If one wanted to pre-allocate all the buckets necessary to meet the needs
     * of the requested count it would be done like this:
     *
     * table->segment_count = MIN((count + table->segment_size-1) / table->segment_size,
     *                            table->directory_size);
     *
     * But with dynamic hash tables there is little point to this, the whole idea is to
     * allow the table to grow/shrink dynamically, therefore we start with just one
     * segment of buckets, the minimum necessary.
     */
    table->segment_count = 1;
    table->p = 0;
    table->entry_count = 0;
    table->delete_callback = delete_callback;
    table->delete_pvt = delete_private_data;

    /*
     * Allocate initial segments of buckets
     */
    for (i = 0; i < table->segment_count; i++) {
        table->directory[i] = (segment_t *)halloc(table, table->segment_size * sizeof(segment_t));
        if (table->directory[i] == NULL) {
            hash_destroy(table);
            return HASH_ERROR_NO_MEMORY;
        }
        memset(table->directory[i], 0, table->segment_size * sizeof(segment_t));
    }
    table->bucket_count = table->segment_count << table->segment_size_shift;
    table->maxp = table->bucket_count;
    table->min_load_factor = min_load_factor == 0 ? HASH_DEFAULT_MIN_LOAD_FACTOR : min_load_factor;
    table->max_load_factor = max_load_factor == 0 ? HASH_DEFAULT_MAX_LOAD_FACTOR : max_load_factor;

#if DEBUG
    if (debug_level >= 1) {
        fprintf(stderr, "hash_create_ex: count=%lu available buckets=%lu bucket_count=%lu maxp=%lu\n",
                count, table->directory_size*table->segment_size, table->bucket_count, table->maxp);
        fprintf(stderr, "                directory_bits=%u segment_bits=%u requested_bits=%u\n",
                directory_bits, segment_bits, requested_bits);
        fprintf(stderr, "                directory_size=%lu segment_size=%lu segment_count=%lu\n",
                table->directory_size, table->segment_size, table->segment_count);
        fprintf(stderr, "                min_load_factor=%lu max_load_factor=%lu\n",
                table->min_load_factor, table->max_load_factor);
    }
#endif
#ifdef HASH_STATISTICS
    memset(&table->statistics, 0, sizeof(table->statistics));
#endif

    *tbl = table;
    return HASH_SUCCESS;
}

#ifdef HASH_STATISTICS
int hash_get_statistics(hash_table_t *table, hash_statistics_t *statistics)
{
    if (!table) return HASH_ERROR_BAD_TABLE;
    if (!statistics) return EINVAL;

    *statistics = table->statistics;

    return HASH_SUCCESS;
}
#endif

int hash_destroy(hash_table_t *table)
{
    unsigned long i, j;
    segment_t *s;
    element_t *p, *q;

    if (!table) return HASH_ERROR_BAD_TABLE;

    if (table != NULL) {
        if (table->directory) {
            for (i = 0; i < table->segment_count; i++) {
                /* test probably unnecessary */
                if ((s = table->directory[i]) != NULL) {
                    for (j = 0; j < table->segment_size; j++) {
                        p = s[j];
                        while (p != NULL) {
                            q = p->next;
                            hdelete_callback(table, HASH_TABLE_DESTROY, &p->entry);
                            if (p->entry.key.type == HASH_KEY_STRING) {
                                hfree(table, (char *)p->entry.key.str);
                            }
                            hfree(table, (char *)p);
                            p = q;
                        }
                    }
                    hfree(table, s);
                }
            }
            hfree(table, table->directory);
        }
        hfree(table, table);
        table = NULL;
    }
    return HASH_SUCCESS;
}

int hash_iterate(hash_table_t *table, hash_iterate_callback callback, void *user_data)
{
    unsigned long i, j;
    segment_t *s;
    element_t *p;

    if (!table) return HASH_ERROR_BAD_TABLE;

    if (table != NULL) {
        for (i = 0; i < table->segment_count; i++) {
            /* test probably unnecessary */
            if ((s = table->directory[i]) != NULL) {
                for (j = 0; j < table->segment_size; j++) {
                    p = s[j];
                    while (p != NULL) {
                        if(!(*callback)(&p->entry, user_data)) return HASH_SUCCESS;
                        p = p->next;
                    }
                }
            }
        }
    }
    return HASH_SUCCESS;
}

static hash_entry_t *hash_iter_next(struct hash_iter_context_t *iter_arg)
{
    struct _hash_iter_context_t *iter = (struct _hash_iter_context_t *) iter_arg;
    hash_entry_t *entry;

    if (iter->table == NULL) return NULL;
    goto state_3a;

 state_1:
    iter->i++;
    if(iter->i >= iter->table->segment_count) return NULL;
    /* test probably unnecessary */
    iter->s = iter->table->directory[iter->i];
    if (iter->s == NULL) goto state_1;
    iter->j = 0;
 state_2:
    if (iter->j >= iter->table->segment_size) goto state_1;
    iter->p = iter->s[iter->j];
 state_3a:
    if (iter->p == NULL) goto state_3b;
    entry = &iter->p->entry;
    iter->p = iter->p->next;
    return entry;
 state_3b:
    iter->j++;
    goto state_2;

    /* Should never reach here */
    fprintf(stderr, "ERROR hash_iter_next reached invalid state\n");
    return NULL;
}

struct hash_iter_context_t *new_hash_iter_context(hash_table_t *table)
{
    struct _hash_iter_context_t *iter;

    if (!table) return NULL;;

    iter = halloc(table, sizeof(struct _hash_iter_context_t));
    if (iter == NULL) {
        return NULL;
    }


    iter->iter.next = (hash_iter_next_t) hash_iter_next;

    iter->table = table;
    iter->i = 0;
    iter->j = 0;
    iter->s = table->directory[iter->i];
    iter->p = iter->s[iter->j];

    return (struct hash_iter_context_t *)iter;
}

unsigned long hash_count(hash_table_t *table)
{
    return table->entry_count;
}


int hash_keys(hash_table_t *table, unsigned long *count_arg, hash_key_t **keys_arg)
{
    unsigned long count = table->entry_count;
    hash_key_t *keys;
    hash_keys_callback_data_t data;

    if (!table) return HASH_ERROR_BAD_TABLE;

    if (count == 0) {
        *count_arg = 0;
        *keys_arg = NULL;
        return HASH_SUCCESS;
    }

    keys = halloc(table, sizeof(hash_key_t) * count);
    if (keys == NULL) {
        *count_arg = -1;
        *keys_arg = NULL;
        return HASH_ERROR_NO_MEMORY;
    }

    data.index = 0;
    data.keys = keys;

    hash_iterate(table, hash_keys_callback, &data);

    *count_arg = count;
    *keys_arg = keys;
    return HASH_SUCCESS;
}

int hash_values(hash_table_t *table, unsigned long *count_arg, hash_value_t **values_arg)
{
    unsigned long count = table->entry_count;
    hash_value_t *values;
    hash_values_callback_data_t data;

    if (!table) return HASH_ERROR_BAD_TABLE;

    if (count == 0) {
        *count_arg = 0;
        *values_arg = NULL;
        return HASH_SUCCESS;
    }

    values = halloc(table, sizeof(hash_value_t) * count);
    if (values == NULL) {
        *count_arg = -1;
        *values_arg = NULL;
        return HASH_ERROR_NO_MEMORY;
    }

    data.index = 0;
    data.values = values;

    hash_iterate(table, hash_values_callback, &data);

    *count_arg = count;
    *values_arg = values;
    return HASH_SUCCESS;
}

typedef struct hash_entries_callback_data_t {
    unsigned long index;
    hash_entry_t *entries;
} hash_entries_callback_data_t;

static bool hash_entries_callback(hash_entry_t *item, void *user_data)
{
    hash_entries_callback_data_t *data = (hash_entries_callback_data_t *)user_data;

    data->entries[data->index++] = *item;
    return true;
}

int hash_entries(hash_table_t *table, unsigned long *count_arg, hash_entry_t **entries_arg)
{
    unsigned long count = table->entry_count;
    hash_entry_t *entries;
    hash_entries_callback_data_t data;

    if (!table) return HASH_ERROR_BAD_TABLE;

    if (count == 0) {
        *count_arg = 0;
        *entries_arg = NULL;
        return HASH_SUCCESS;
    }

    entries = halloc(table, sizeof(hash_entry_t) * count);
    if (entries == NULL) {
        *count_arg = -1;
        *entries_arg = NULL;
        return HASH_ERROR_NO_MEMORY;
    }

    data.index = 0;
    data.entries = entries;

    hash_iterate(table, hash_entries_callback, &data);

    *count_arg = count;
    *entries_arg = entries;
    return HASH_SUCCESS;
}

bool hash_has_key(hash_table_t *table, hash_key_t *key)
{
    hash_value_t value;

    if (hash_lookup(table, key, &value) == HASH_SUCCESS)
        return true;
    else
        return false;
}


int hash_get_default(hash_table_t *table, hash_key_t *key, hash_value_t *value, hash_value_t *default_value)
{
    int error;

    if (!table) return HASH_ERROR_BAD_TABLE;

    if ((error = hash_lookup(table, key, value)) != HASH_SUCCESS) {
        if ((error = hash_enter(table, key, default_value)) != HASH_SUCCESS) {
            return error;
        }
        *value = *default_value;
        return HASH_SUCCESS;
    }

    return HASH_SUCCESS;
}

int hash_enter(hash_table_t *table, hash_key_t *key, hash_value_t *value)
{
    int error;
    segment_t element, *chain;
    size_t len;

    if (!table) return HASH_ERROR_BAD_TABLE;

    if (!is_valid_key_type(key->type))
        return HASH_ERROR_BAD_KEY_TYPE;

    if (!is_valid_value_type(value->type))
        return HASH_ERROR_BAD_VALUE_TYPE;

    lookup(table, key, &element, &chain);

    if (element == NULL) {                    /* not found */
        element = (element_t *)halloc(table, sizeof(element_t));
        if (element == NULL) {
            /* Allocation failed, return NULL */
            return HASH_ERROR_NO_MEMORY;
        }
        memset(element, 0, sizeof(element_t));
        /*
         * Initialize new element
         */
        switch(element->entry.key.type = key->type) {
        case HASH_KEY_ULONG:
            element->entry.key.ul = key->ul;
            break;
        case HASH_KEY_STRING:
            len = strlen(key->str)+1;
            element->entry.key.str = halloc(table, len);
            if (element->entry.key.str == NULL) {
                hfree(table, element);
                return HASH_ERROR_NO_MEMORY;
            }
            memcpy((void *)element->entry.key.str, key->str, len);
            break;
        }

        *chain = element;             /* link into chain */
        element->next = NULL;

        /*
         * Table over-full?
         */
        if (++table->entry_count / table->bucket_count > table->max_load_factor) {
            if ((error = expand_table(table)) != HASH_SUCCESS) { /* doesn't affect element */
                return error;
            }
        }

    } else {
        hdelete_callback(table, HASH_ENTRY_DESTROY, &element->entry);
    }

    switch(element->entry.value.type = value->type) {
    case HASH_VALUE_UNDEF:
        element->entry.value.ul = 0;
        break;
    case HASH_VALUE_PTR:
        element->entry.value.ptr = value->ptr;
        break;
    case HASH_VALUE_INT:
        element->entry.value.i = value->i;
        break;
    case HASH_VALUE_UINT:
        element->entry.value.ui = value->ui;
        break;
    case HASH_VALUE_LONG:
        element->entry.value.l = value->l;
        break;
    case HASH_VALUE_ULONG:
        element->entry.value.ul = value->ul;
        break;
    case HASH_VALUE_FLOAT:
        element->entry.value.f = value->f;
        break;
    case HASH_VALUE_DOUBLE:
        element->entry.value.d = value->d;
        break;
    }

    return HASH_SUCCESS;
}

int hash_lookup(hash_table_t *table, hash_key_t *key, hash_value_t *value)
{
    segment_t element, *chain;

    if (!table) return HASH_ERROR_BAD_TABLE;

    if (!is_valid_key_type(key->type))
        return HASH_ERROR_BAD_KEY_TYPE;

    lookup(table, key, &element, &chain);

    if (element) {
        *value = element->entry.value;
        return HASH_SUCCESS;
    } else {
        return HASH_ERROR_KEY_NOT_FOUND;
    }
}

int hash_delete(hash_table_t *table, hash_key_t *key)
{
    int error;
    segment_t element, *chain;

    if (!table) return HASH_ERROR_BAD_TABLE;

    if (!is_valid_key_type(key->type))
        return HASH_ERROR_BAD_KEY_TYPE;

    lookup(table, key, &element, &chain);

    if (element) {
        hdelete_callback(table, HASH_ENTRY_DESTROY, &element->entry);
        *chain = element->next; /* remove from chain */
        /*
         * Table too sparse?
         */
        if (--table->entry_count / table->bucket_count < table->min_load_factor) {
            if ((error = contract_table(table)) != HASH_SUCCESS) { /* doesn't affect element */
                return error;
            }
        }
        if (element->entry.key.type == HASH_KEY_STRING) {
            hfree(table, (char *)element->entry.key.str);
        }
        hfree(table, element);
        return HASH_SUCCESS;
    } else {
        return HASH_ERROR_KEY_NOT_FOUND;
    }
}


