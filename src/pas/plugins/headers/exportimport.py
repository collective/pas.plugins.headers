# -*- coding: utf-8 -*-
from pas.plugins.headers.plugins import HeaderPlugin
from pas.plugins.headers.utils import get_plugin
from pas.plugins.headers.utils import PLUGIN_ID

import json


FILENAME = 'pas.plugins.headers.json'


def import_properties(context):
    """Import HeaderPlugin properties.
    """
    site = context.getSite()
    body = context.readDataFile(FILENAME)
    logger = context.getLogger(PLUGIN_ID)
    if not body:
        logger.info('%s not found or empty.', FILENAME)
        return
    plugin = get_plugin(site)
    if plugin is None:
        logger.debug('Plugin not found.')
        return
    # Maybe catch ValueError.  But it gives a clear error message.
    props = json.loads(body)
    if not isinstance(props, dict):
        # logger.error('%s does not contain a json dictionary.', FILENAME)
        # return
        raise ValueError(
            '{0} does not contain a json dictionary.'.format(FILENAME))
    purge = props.pop('purge', False)
    if purge:
        for prop_name in plugin.propertyIds():
            default = getattr(HeaderPlugin, prop_name)
            setattr(plugin, prop_name, default)
        logger.info('Purge: HeaderPlugin properties reset to defaults.')
    for prop_name, prop_value in props.items():
        if prop_name not in plugin.propertyIds():
            logger.info('Ignoring unknown property id %s.', prop_name)
            continue
        # When saving in the ZMI, you always get a string,
        # so we want this for import too.
        if isinstance(prop_value, unicode):
            prop_value = prop_value.encode('utf-8')
        elif isinstance(prop_value, list):
            if prop_value and isinstance(prop_value[0], unicode):
                prop_value = [v.encode('utf-8') for v in prop_value]
        logger.debug('Setting %s to %r', prop_name, prop_value)
        # Note that lists are automatically turned into tuples.
        plugin._setPropValue(prop_name, prop_value)
    logger.info('Imported HeaderPlugin properties.')


def export_properties(context):
    """Export HeaderPlugin properties.
    """
    site = context.getSite()
    logger = context.getLogger(PLUGIN_ID)
    plugin = get_plugin(site)
    if plugin is None:
        return
    body = json.dumps(dict(plugin.propertyItems()), sort_keys=True, indent=4)
    context.writeDataFile(FILENAME, body, 'application/json')
    logger.info('Exported HeaderPlugin properties.')
