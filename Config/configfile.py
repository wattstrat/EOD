import Config.config as config
defaultconfig = {
    'common': {
        'pidfile': '/var/run/WattStrat/METEOR.pid',
        'loglevel': 0,
        'logconfigfile': '/etc/meteor/logger.conf',

        'mongo_host': config.MONGO_SERVER_ADDRESS,
        'mongo_port': config.MONGO_SERVER_PORT,
        'mongo_db': config.MONGODB_METEOR_DATABASE,

        'redis_host': config.REDIS_HOST,
        'redis_port': config.REDIS_PORT,

        'cache': 'Politics.ListedDataCalculus',
        'cache_opt': {
            'caches':
            [
                {
                    'type': 'Cache.RAM',
                },
                {
                    'type': 'Cache.VariablesSharedRAM'
                }
            ],
            'saveAll': True,
        }
        # 'cache_opt': { 'saveAll': True, 'caches': [{
        #     'type': '',
        #     'args': '',
        #     'kwargs': '',
        #     'ElSized': {},
        #     'Sized': {},
        #     'local': False,
        #     'remote': False,
        # }]
    }
}
