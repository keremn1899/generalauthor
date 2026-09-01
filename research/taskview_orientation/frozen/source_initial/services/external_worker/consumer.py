from runtime.consumer_registry import resolve_consumer


def start_worker(tenant_alias: str, plugin_loader) -> object:
    consumer_path = resolve_consumer(tenant_alias)
    return plugin_loader.load(consumer_path)

