import asyncio
from _contextvars import ContextVar,Token

_req_context_var=ContextVar("req_id",default="")

def set_req_id(req_id:str)->Token:
    return _req_context_var.set(req_id)

def get_req_id()->Token:
    return _req_context_var.get()
def reset_req_id(token:Token):
    _req_context_var.reset(token)


if __name__=="__main__":
    async def req1():
        print(f"before req1 req_id= {get_req_id()}")
        token = set_req_id("1111")
        await asyncio.sleep(1) # 模拟处理一定的时间
        token=set_req_id("2222")
        print(f"after req1 req_id= {get_req_id()}")
        reset_req_id(token)
        print(f"after reset req1 req_id= {get_req_id()}")

    async def req2():
        print(f"before req2 req_id= {get_req_id()}")
        token = set_req_id("2222")
        await asyncio.sleep(1)  # 模拟处理一定的时间
        print(f"after req2 req_id= {get_req_id()}")
        reset_req_id(token)
        print(f"after reset req2 req_id= {get_req_id()}")

    async def test():
        await asyncio.gather(req1(), req2())

    asyncio.run(test())