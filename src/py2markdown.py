import sys
from pathlib import Path
from typing import List, Union, Optional


class PyClass(object):
    def __init__(self, line):
        self.name = extract_name(line, 'class')
        self.super_class = extract_inside_bracket(line)
        self.description = ''
        self.code = ''

        ParsedText.previous_class = self.name


class PyFunction(object):
    def __init__(self, line):
        self.name = extract_name(line, 'def')
        self.args = parse_args(extract_inside_bracket(line))
        self.return_value = get_return(line)
        self.description = ''
        self.code = ''
    

class PyMethod(PyFunction):
    def __init__(self, line):
        super().__init__(line)
        self.class_name = ParsedText.previous_class
        self.return_value = get_return(line)
        self.description = ''
        self.code = ''


class ParsedText(object):
    """
    For convert source code to markdown.
    """
    previous_class = None
    def __init__(self, path):
        self.path = path
        self.text_list = self.path.read_text().splitlines()
        
        #result = ['[[toc]]']
        result = ['']
        for obj in self.parse():
            if isinstance(obj, PyClass):
                result.append(f"# **{obj.name}** *extends {obj.super_class}*")
                result.append(f"::: tip Description  \n{obj.description if obj.description else 'None'}  \n:::\n")
            if isinstance(obj, PyFunction):
                depth = '' if type(obj) == PyFunction else '#'
                class_name = getattr(obj, 'class_name', '')
                result.append(f"#{depth} {class_name + '.' if class_name else ''}{obj.name}({format_args(obj.args)}) -> {obj.return_value}")
                result.append(f"::: tip Description  \n{obj.description if obj.description else 'None'}  \n:::\n")
                result.append(f"##{depth} Code\n```python\n{obj.code}\n```\n")

            result.append('<br><br>\n')
        
        self.markdown = '\n'.join(result)
        
    def write_file(self, output_path) -> None:
        file_path = output_path / self.path.with_suffix('').with_suffix('.md')
        print(f"write: {file_path}")
        if not file_path.parent.exists():
            file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(self.markdown)
    
    def parse(self) -> List[Union[PyClass, PyMethod, PyFunction]]:
        result = []
        comment_buffer = []
        is_into_comment = False

        code_buffer = []
        code_nest = 0

        for line in self.text_list:
            code_buffer.append(line)

            nest = get_nest_level(line)
            line = line.strip()

            if 1<len(result):
                if nest < code_nest and line is not '' or line.startswith('class ') and 3<len(code_buffer) or line.startswith('def ') and 3<len(code_buffer):
                    for num, p_line in enumerate(reversed(code_buffer[:-1])):
                        if p_line.strip() is not '':
                            break

                    result[-1].code = '\n'.join([c_line.replace('    ', '', code_nest) for c_line in code_buffer[:-(num + 1)]])
            
            # classify
            if line.startswith('class '):
                result.append(PyClass(line))

                code_buffer = [code_buffer[-1]]
                code_nest = nest

            if line.startswith('def '):
                if nest == 1:
                    result.append(PyMethod(line))
                else:
                    result.append(PyFunction(line))

                code_buffer = [code_buffer[-1]]
                code_nest = nest

            
            # comment detection
            if is_into_comment:
                comment_buffer.append(line)

            if '\"\"\"' in line:
                if not is_into_comment:
                    is_into_comment = True
                    comment_buffer.clear()
                    comment_buffer.append(line)
                else:
                    is_into_comment = False
                    result[-1].description = '\n'.join([line.replace('"""', '').strip() for line in comment_buffer if line.replace('"""', '').strip()])
                    comment_buffer.clear()

        result[-1].code = '\n'.join([c_line.replace('    ', '', code_nest) for c_line in code_buffer])
        return result


def extract_name(line: str, prefix: str) -> str:
    return line.replace(f"{prefix} ", '').split('(')[0].replace('_', '\_')

def extract_inside_bracket(line: str) -> str:
    return line.split('(')[1].split(')')[0] 

def parse_args(line: str) -> List[str]:
    args = [arg.strip() for arg in line.split(',')]
    return args if args != [''] else ['None']
    
def get_nest_level(line: str) -> int:
    return len(line.split('    ')) - 1

def get_return(line: str) -> str:
    return line.split('->')[-1].strip()[:-1] if '->' in line else 'Any'

def format_args(args: List[str]) -> str:
    return ', '.join([arg for arg in args])


def main():
    dir_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    py_files = dir_path.glob('**/*.py')
    for file in py_files:
        try:
            p = ParsedText(path=file)
            p.write_file(output_path)
        except:
            pass

if __name__ == '__main__':
    main()