import ast
import os
import collections
import argparse
import git
import json
import csv

from nltk import pos_tag


class Downloader:

    """ Copy GitHab repo by user link  """

    def __init__(self):
        pass

    def make_repo_clone(self, git_url):
        repo_dir = git_url.split('/')[-1]
        if not os.path.exists(f'./{repo_dir}'):
            new_repo = git.Repo.clone_from(git_url, repo_dir)
        return repo_dir


class UserInput:

    """ Parsing arguments and saving data into class variables """

    def __init__(self):
        self.user_input = []

    def argument_parser(self):
        parser = argparse.ArgumentParser(description='The module creates a report of a static search for top words used '
                                                     'in python files in a chosen directory')
        parser.add_argument('word_type', type=str,
                            help='VB - verb, CC - conjunction, IN - preposition, NN - a noun, JJ - adjective, '
                                 'RB - adverbs, ANY - any words')
        parser.add_argument('searching_level', type=str,
                            help='Use NAMES for searching in functions names or INSIDE for search through variables')
        parser.add_argument('report_type', type=str,
                            help='Input CONS for print out to terminal, FILE.CSV or FILE.JSON for saving in file')
        parser.add_argument('dir_name', type=str, help='Input directory name or link to repo')
        args = parser.parse_args()
        self.user_input = [args.word_type, args.searching_level, args.report_type, args.dir_name]

    def what_we_searching(self):
        return self.user_input[0]

    def names_or_inside(self):
        return self.user_input[1]

    def report_type(self):
        return self.user_input[2]

    def where_to_search(self):
        return self.user_input[3]


class TreeMaker:

    """ creating a data tree and divides the tree into words """

    def create_filenames_list(self, path_to):
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

    def get_trees(self, path_to, with_filenames=False, with_file_content=False):

        filenames = self.create_filenames_list(path_to)
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


class WordCounter(TreeMaker):
    """ Counting words """

    def flat(self, _list):
        """ [(1,2), (3,4)] -> [1, 2, 3, 4]"""
        return sum([list(item) for item in _list], [])

    def find_type(self, word, word_type):
        """ word_type: VB - verb, CC - conjunction, IN - preposition, NN - a noun, JJ - adjective, RB - adverbs, ANY """
        if not word:
            return False
        pos_info = pos_tag([word])
        return pos_info[0][1] == word_type

    def split_snake_case_name_to_words(self, name):
        return [n for n in name.split('_') if n]

    def get_all_names(self, tree):
        return [node.id for node in ast.walk(tree) if isinstance(node, ast.Name)]

    def get_all_words(self, path_to):
        """" Return cleared list of words WITHOUT type definition """
        trees = [t for t in self.get_trees(path_to) if t]
        function_names = [f for f in self.flat([self.get_all_names(t) for t in trees]) if
                          not (f.startswith('__') and f.endswith('__'))]
        return self.flat([self.split_snake_case_name_to_words(function_name) for function_name in function_names])

    def get_words_from_function_name(self, function_name, word_type):
        return [word for word in function_name.split('_') if self.find_type(word, word_type)]

    def get_top_words_in_path(self, path_to, word_type, top_size=10, returning=False):
        """ Return top words from functions names """
        trees = [t for t in super().get_trees(path_to) if t]
        functions_list = [f for f in self.flat(
            [[node.name.lower() for node in ast.walk(t) if isinstance(node, ast.FunctionDef)] for t in trees]) if
                          not (f.startswith('__') and f.endswith('__'))]
        print('functions extracted')
        words = self.flat(
            [self.get_words_from_function_name(function_name, word_type) for function_name in functions_list])
        if returning:
            return words
        return collections.Counter(words).most_common(top_size)

    def get_top_variables_names(self, path_to, word_type, top_size=10):
        """ Return top words from variables names """
        all_words = self.get_all_words(path_to)
        words_in_function_names = self.get_top_words_in_path(path_to, word_type, returning=True)
        cleared_words = [word for word in all_words if self.find_type(word, word_type)]
        for _ in words_in_function_names:
            try:
                cleared_words.remove(_)
            except ValueError:
                continue
        return collections.Counter(cleared_words).most_common(top_size)

    def get_top_any(self, path_to, top_size=10):
        """ Return top words without type definition """
        all_words = self.get_all_words(path_to)
        return collections.Counter(all_words).most_common(top_size)


class Writer:

    """ Creates a report """

    def report_to_console(self, word_counter_inst):
        print('#-#-#- RESULT -#-#-#')
        print('total %s words, %s unique' % (len(word_counter_inst), len(set(word_counter_inst))))
        for word, occurence in word_counter_inst:
            print(f'Word "{word}" has been found {occurence} times')

    def save_report_in_file(self, file_type, data_to_save):
        print('Saving searching result in file')
        formats = {
            'FILE.CSV': 'csv',
            'FILE.JSON': 'json'
        }
        try:
            f = open(f'report.{formats[file_type]}')
            f.close()
        except FileNotFoundError:
            if formats[file_type] == 'json':
                report_data_json = {}
                for word, occurence in data_to_save:
                    report_data_json.setdefault(word, occurence)
                with open(f'report.{formats[file_type]}', 'w', encoding='utf-8') as f:
                    json.dump(report_data_json, f)
            else:
                report_data_csv = []
                for element in data_to_save:
                    report_data_csv.append(element)
                with open(f'report.{formats[file_type]}', 'w', encoding='utf-8') as f:
                    report_writer = csv.writer(f)
                    report_writer.writerows(report_data_csv)


if __name__ == '__main__':
    downloader = Downloader()
    user_data = UserInput()
    tree_maker = TreeMaker()
    word_counter = WordCounter()
    writer = Writer()

    user_data.argument_parser()

    user_data_list = {
        'word_type': user_data.what_we_searching(),
        'searching_level': user_data.names_or_inside(),
        'report_type': user_data.report_type(),
        'dir_name': user_data.where_to_search()
    }

    if user_data_list['dir_name'].startswith('http'):
        user_data_list.update({'dir_name': downloader.make_repo_clone(user_data_list['dir_name'])})

    path = os.path.join('.', user_data_list['dir_name'])

    if user_data_list['word_type'] == 'ANY':
        if user_data_list['report_type'] == 'CONS':
            writer.report_to_console(word_counter.get_top_any(path))
        else:
            writer.save_report_in_file(user_data_list['report_type'], word_counter.get_top_any(path))
    elif user_data_list['searching_level'] == 'INSIDE':
        if user_data_list['report_type'] == 'CONS':
            writer.report_to_console(word_counter.get_top_words_in_path(path, user_data_list['word_type']))
        else:
            writer.save_report_in_file(user_data_list['report_type'], word_counter.get_top_variables_names(path, user_data_list['word_type']))
    else:
        if user_data_list['report_type'] == 'CONS':
            writer.report_to_console(word_counter.get_top_words_in_path(path, user_data_list['word_type']))
        else:
            writer.save_report_in_file(user_data_list['report_type'], word_counter.get_top_words_in_path(path, user_data_list['word_type']))

