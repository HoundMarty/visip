import os
import io
import attr
import subprocess

from typing import *
from ..dev import base, exceptions as exc
from ..dev import dtype, data
from ..code import decorators
from ..dev import tools

# @decorators.Enum
# class FileMode:
#     read = 0
#     write = 1

Folder = NewType('Folder', str)
FileOut = NewType('FileOut', str)

@attr.s(auto_attribs=True)
class FileIn(dtype.DataClassBase):
    """
    Represent an existing input file.
    TODO: In fact we need to represent only already existiong input files.
    The output files are just path, no hash. So possibly define these
    two as separate types.
    """
    path: str
    hash: int

    def __str__(self):
        return self.path

@attr.s(auto_attribs=True)
class ExecResult(dtype.DataClassBase):
    args: List[str]
    return_code: int
    workdir: Folder
    stdout: str  # Exists when result is available.
    stderr: str


@decorators.action_def
def file_in(path: str, workspace: Folder = "") -> FileIn:
    # we assume to be in the root of the VISIP workspace
    full_path = os.path.abspath(os.path.join(workspace, path))
    # path relative to the root
    if os.path.isfile(full_path):
        return FileIn(path=full_path, hash=data.hash_file(full_path))
    else:
        print("err cwd", os.getcwd())
        raise exc.ExcVFileNotFound(full_path)


@decorators.action_def
def file_out(path: str, workspace: Folder = "") -> FileOut:
    # we assume to be in the root of the VISIP workspace
    full_path = os.path.join(workspace, path)
    # path relative to the root
    if os.path.isfile(full_path):
        raise exc.ExcVWrongFileMode("Existing output file: " + full_path)
    else:
        return FileOut(full_path)



@decorators.Enum
class SysFile:
    PIPE = subprocess.PIPE
    STDOUT = subprocess.STDOUT
    DEVNULL = subprocess.DEVNULL


Command = NewType('Command', List[Union[str, FileIn]])
Redirection = NewType('Redirection', Union[FileOut, None, SysFile])

def _subprocess_handle(redirection):
    if type(redirection) is str:    # TODO: should be FileOut
        return open(redirection, "w")
    return redirection


@decorators.action_def
def system(arguments: Command, stdout: Redirection = None, stderr: Redirection = None, workdir:str = '') -> ExecResult:
    """
    Execute a system command.  No support for portability.
    The files in the 'arguments' are converted to the file names.
    arguments[0] is the command path.
    Commmand line is composed from the (quoted) arguments separated by the space.
    See: [Subprocess doc](https://docs.python.org/3/library/subprocess.html)

    TODO: Some support for piped actions, i.e. when one action produce a sequence of values, we can process them
    in pipline fassin. Here we can treat stdout as a sequence of lines and thus pipe them to other process
    through the POpen piping.
    """
    with tools.change_cwd(workdir):
        subprocess.PIPE
        args = [str(arg) for arg in arguments]
        stdout = _subprocess_handle(stdout)
        stderr = _subprocess_handle(stderr)
        result = subprocess.run(args, stdout=stdout, stderr=stderr)
        exec_result = ExecResult(
            args=args,
            return_code=result.returncode,
            workdir=os.getcwd(),
            stdout=result.stdout,
            stderr=result.stderr
        )
        try:
            stdout.close()
            stderr.close()
        except AttributeError:
            pass
        if exec_result.return_code != 0:
            exc.ExcVCommandFailed(str(args), exec_result)

        return exec_result

@decorators.action_def
def derived_file(f: FileIn, ext:str) -> FileOut:
    base, old_ext = os.path.splitext (f.path)
    new_file_name = base + ext
    return file_out.call(new_file_name)

@decorators.action_def
def format(format_str: str, *args : Any) -> str:
    return format_str.format(*args)

@decorators.action_def
def file_from_template(template: dtype.Constant[FileIn],
                       parameters: Dict,
                       delimiters:dtype.Constant[str]="<>") -> FileIn:
    """
    Substitute for placeholders of format '<name>' from the dict 'params'.
    :param file_in: Template file with extension '.tmpl'.
    :param file_out: Values substituted.
    :param params: { 'name': value, ...}
    """
    if os.path.splitext(template.path)[1] != ".tmpl":
        exc.ExcVFileNotFound("File template must have '.tmpl' extension, get path: {}".format(template.path))
    used_params = []
    with open(template.path, 'r') as src:
        text = src.read()
    for name, value in parameters.items():
        placeholder = '{}{}{}'.format(delimiters[0], name, delimiters[1])
        n_repl = text.count(placeholder)
        if n_repl > 0:
            used_params.append(name)
            text = text.replace(placeholder, str(value))
    file_out = derived_file.call(template, '')
    with open(file_out, 'w') as dst:
        dst.write(text)

    return file_in.call(file_out)

#
# def system_script(commands: List[Command]):
#     pass