# -*- coding:utf-8 -*-


class ConsumerAppRouter(object):
    """
    控制 Consumer App 应用中模型的
    所有数据库操作的路由
    """
    def db_for_read(self, model, **hints):
        module_name = self.get_module_name(model)
        if module_name == 'Consumer_App':
            return 'consumer'
        return None

    def db_for_write(self, model, **hints):
        module_name = self.get_module_name(model)
        if module_name == 'Consumer_App':
            return 'consumer'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        obj1_module_name = self.get_module_name(obj1)
        obj2_module_name = self.get_module_name(obj2)
        if obj1_module_name == 'Consumer_App' or obj2_module_name == 'Consumer_App':
            return True
        return None

    def allow_syncdb(self, db, model):
        if db == 'consumer':
            return model._meta.app_label == 'Consumer_App'
        elif model._meta.app_label == 'Consumer_App':
            return False
        return None

    @classmethod
    def get_module_name(cls, model):
        return model._meta.model.__module__.split('.', 1)[0]
