import ast
from html import escape

from .. import loader, utils
from telethon.tl.types import Message

async def insert_returns(body):
    if isinstance(body[-1], ast.Expr):
        body[-1] = ast.Return(body[-1].value)
        ast.fix_missing_locations(body[-1])
        if isinstance(body[-1], ast.If):
            await insert_returns(body[-1].body)
            await insert_returns(body[-1].orelse)
        if isinstance(body[-1], ast.With):
            await insert_returns(body[-1].body)

async def execute_python_code(code, env={}):
    try:
        fn_name = "_eval_expr"
        cmd = "\n".join(f" {i}" for i in code.splitlines())
        body = f"async def {fn_name}():\n{cmd}"
        parsed = ast.parse(body)
        body = parsed.body[0].body
        await insert_returns(body)
        env = {'__import__': __import__, **env}
        exec(compile(parsed, filename="<ast>", mode="exec"), env)
        return (await eval(f"{fn_name}()", env))
    except Exception as error:
        return error

class EvalMod(loader.Module):
    """Используйте eval прямо через Material!"""

    strings = {'name': 'Eval'}
    
    async def ecmd(self, message: Message):
        """Запустить команду eval на языке Python"""
        args = utils.get_args_raw(message)
        result = await execute_python_code(
            args,
            {
                'self': self,
                'client': self._client,
                'app': self._client,
                'utils': utils,
                'loader': loader,
                'telethon': __import__('telethon'),
                'message': message,
                'args': args,
            }
        )

        if getattr(result, 'stringify', ''):
            try:
                result = str(result.stringify())
            except:
                pass

        await utils.answer(
            message,
            "<b>🐍 Code</b>:\n"
            f"<code>{args}</code>\n"
            "<b>💻 Output</b>:\n"
            f"<code>{escape(result)}</code>"
        )