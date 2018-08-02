# -*- coding: utf-8 -*-
from pas.plugins.headers.plugins import HeaderPlugin
from pas.plugins.headers.utils import get_plugin

import json


FILENAME = 'pas.plugins.headers.json'


def import_properties(context):
    """Import HeaderPlugin properties.
    """
    site = context.getSite()
    body = context.readDataFile(FILENAME)
    logger = context.getLogger('request_headers')
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
        logger.error('%s does not contain a json dictionary.', FILENAME)
        return
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
        logger.info('Setting %s to %r', prop_name, prop_value)
        # TODO force ascii?
        plugin._setPropValue(prop_name, prop_value)
    logger.info('Imported HeaderPlugin properties.')


def export_properties(context):
    """Export HeaderPlugin properties.
    """
    site = context.getSite()
    logger = context.getLogger('request_headers')
    plugin = get_plugin(site)
    if plugin is None:
        return
    body = json.dumps(dict(plugin.propertyItems()), sort_keys=True, indent=4)
    context.writeDataFile(FILENAME, body, 'application/json')
    logger.info('Exported HeaderPlugin properties.')
