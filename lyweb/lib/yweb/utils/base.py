import os
import logging


def makesure_path_exist( path ):

    if os.path.exists( path ):
        return True

    logging.warn( _('%s does not exist, try to create.') % path )

    try:
        os.makedirs( path )
        return True

    except Exception, e:
        logging.error( _('create "%(dir)s" failed: %(emsg)s') % {
                'dir': path, 'emsg': e } )

        return False
