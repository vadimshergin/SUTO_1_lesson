import ast
import os
import collections

from nltk import pos_tag

#TODO * выдавать статистику самых частых слов по глаголам или существительным (в зависимости от параметра отчёта);
#TODO * выдавать статистику самых частых слов названия функций или локальных переменных внутри функций (в зависимости от параметра отчёта);
#TODO * выводить результат в консоль, json-файл или csv-файл (в зависимости от параметра отчёта);
#TODO * принимать все аргументы через консольный интерфейс.
#TODO * клонировать репозитории с Гитхаба;


def flat(_list):
    """ [(1,2), (3,4)] -> [1, 2, 3, 4]"""
    return sum([list(item) for item in _list], [])


def is_verb(word):
    """" Check if a word is verb """
    if not word:
        return False
    pos_info = pos_tag([word])
    return pos_info[0][1] == 'VB'


def create_filenames_list(path_to):
    """" Create list of files placed in certain directories """
    filenames_list = []
    for dirname, dirs, files in os.walk(path_to, topdown=True):
        if len(filenames_list) <= 100:
            for file in files:
                if file.endswith('.py'):
                    filenames_list.append(os.path.join(dirname, file))
        else:
            break
    print('total %s files' % len(filenames_list))
    return filenames_list


def get_trees(path_to, with_filenames=False, with_file_content=False):
    """"
    штука которая создает дерево
    """
    filenames = create_filenames_list(path_to)
    trees = []
    for filename in filenames:
        with open(filename, 'r', encoding='utf-8') as attempt_handler:
            main_file_content = attempt_handler.read()
        try:
            tree = ast.parse(main_file_content)
        except SyntaxError as e:
            print(e)
            tree = None
        if with_filenames:
            if with_file_content:
                trees.append((filename, main_file_content, tree))
            else:
                trees.append((filename, tree))
        else:
            trees.append(tree)
    print('trees generated')
    return trees


def get_all_names(tree):
    return [node.id for node in ast.walk(tree) if isinstance(node, ast.Name)]


def get_verbs_from_function_name(function_name):
    return [word for word in function_name.split('_') if is_verb(word)]


def split_snake_case_name_to_words(name):
    return [n for n in name.split('_') if n]


def get_all_words_in_path(path_to):
    trees = [t for t in get_trees(path_to) if t]
    function_names = [f for f in flat([get_all_names(t) for t in trees]) if not (f.startswith('__') and f.endswith('__'))]
    return flat([split_snake_case_name_to_words(function_name) for function_name in function_names])


def get_top_verbs_in_path(path_to, top_size=10):
    # global Path
    # Path = path
    trees = [t for t in get_trees(path_to) if t]
    functions_list = [f for f in flat([[node.name.lower() for node in ast.walk(t) if isinstance(node, ast.FunctionDef)] for t in trees]) if not (f.startswith('__') and f.endswith('__'))]
    print('functions extracted')
    verbs = flat([get_verbs_from_function_name(function_name) for function_name in functions_list])
    return collections.Counter(verbs).most_common(top_size)


def get_top_functions_names_in_path(path_to, top_size=10):
    t = get_trees(path_to)
    nms = [f for f in flat([[node.name.lower() for node in ast.walk(t) if isinstance(node, ast.FunctionDef)] for t in t]) if not (f.startswith('__') and f.endswith('__'))]
    return collections.Counter(nms).most_common(top_size)


wds = []
projects = ['SUTO_1_lesson']

for project in projects:
    path = os.path.join('.', project)
    wds += get_top_verbs_in_path(path)

top_size = 200
print('#-#-#- RESULT -#-#-#')
print('total %s words, %s unique' % (len(wds), len(set(wds))))
for word, occurence in collections.Counter(wds).most_common(top_size):
    print(f'Word "{word[0]}" has been found {word[1]} times')
