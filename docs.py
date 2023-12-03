from inspect import signature
from typing import NewType

import datapath
import datapath.types

indent_length = 4


def write_doc(f, obj_doc, level=1):
    if not obj_doc.startswith('\n'):
        f.write('\n')
    obj_doc = obj_doc.rstrip()
    for line in obj_doc.splitlines():
        if line.startswith(' ' * indent_length * level):
            f.write(line[indent_length * level:])
        else:
            f.write(line)
        f.write('\n')


def make_docs():
    with open('REFERENCE.md', 'w') as f:
        f.write('# datapath Reference\n\n')
        f.write('## Types\n\n')
        f.write('```\n')
        for obj_name, obj in datapath.types.__dict__.items():
            if isinstance(obj, NewType):
                supertype = str(obj.__supertype__).replace('typing.', '')
                f.write(f'{obj_name} = {supertype}\n')
        f.write('```\n\n')

        f.write('## Public API\n\n')
        f.write('The API semantics are optimized for use with `import datapath`, without any `from` clause\n\n')
        for obj_name in datapath.__all__:
            obj = getattr(datapath, obj_name)
            obj_doc = getattr(obj, '__doc__', None)
            if not obj_doc:
                continue
            do_class = False
            do_sig = False
            suffix = ''
            if isinstance(obj, type):
                if issubclass(obj, Exception):
                    descriptor = 'exception'
                else:
                    descriptor = 'class'
                    do_class = True
                    do_sig = True
            elif callable(obj):
                descriptor = 'function'
                do_sig = True
                suffix = '()'
            else:
                descriptor = 'constant'
            f.write(f'### {descriptor} `{obj_name}{suffix}`\n')
            if do_sig:
                f.write(f'\n```\n{obj_name}{signature(obj)}\n```\n')
            write_doc(f, obj_doc)
            if do_class:
                f.write('\n')
                for attr_name, attr in obj.__dict__.items():
                    if attr_name.startswith('_'):
                        continue
                    attr_doc = getattr(attr, '__doc__', None)
                    if not attr_doc:
                        continue
                    do_sig = False
                    suffix = ''
                    if callable(attr):
                        descriptor = 'method'
                        do_sig = True
                        suffix = '()'
                    else:
                        descriptor = 'attribute'
                    f.write(f'#### {descriptor} `{obj_name}.{attr_name}{suffix}`\n')
                    if do_sig:
                        f.write(f'\n```\n{obj_name}.{attr_name}{signature(attr)}\n```\n')
                    write_doc(f, attr_doc, 2)
                    f.write('\n')
            f.write('\n')


if __name__ == '__main__':
    make_docs()
