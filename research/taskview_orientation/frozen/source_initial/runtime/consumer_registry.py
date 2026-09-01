REGISTRY = {
    "north": "workers.north.JsonConsumer",
    "south": "workers.south.JsonConsumer",
    "*": "plugins.{tenant_alias}.JsonConsumer",
}


def resolve_consumer(tenant_alias: str) -> str:
    target = REGISTRY.get(tenant_alias, REGISTRY["*"])
    return target.format(tenant_alias=tenant_alias)

