"""
初始化i18n配置以防止pygame_gui错误
必须在导入任何pygame_gui模块之前执行
"""
try:
    import i18n
    from i18n import config, resource_loader
    
    # Patch config.get to return sensible defaults
    original_get = config.get
    
    def patched_get(key):
        """Return default values for i18n config to prevent None errors"""
        defaults = {
            'locale': 'en',
            'fallback': 'en',
            'filename_format': '{locale}.{format}',
            'skip_locale_root_data': True,
            'namespace_delimiter': '.',
            'enable_memoization': True
        }
        try:
            result = original_get(key)
        except:
            result = None
        
        if result is None and key in defaults:
            return defaults[key]
        return result
    
    config.get = patched_get
    
    # Patch resource_loader.search_translation to handle None keys
    original_search = resource_loader.search_translation
    
    def patched_search(key, locale):
        """Handle None keys gracefully"""
        if key is None:
            return None
        return original_search(key, locale)
    
    resource_loader.search_translation = patched_search
    
    # Also set the values using i18n.set
    i18n.set('locale', 'en')
    i18n.set('fallback', 'en')
    i18n.set('namespace_delimiter', '.')
    
    print("i18n configured successfully")
except Exception as e:
    print(f"Warning: i18n configuration failed: {e}")
