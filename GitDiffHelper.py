import sublime, sublime_plugin
import git
import os, json

class GitDiffHelperCommand(sublime_plugin.WindowCommand):

    guh_output_view = None
    file_list = None
    settings = {}
    settings_file = None
    main_folder = None

    def run(self):
        self.main_folder = self.window.folders()[0]
        self.settings_file = self.main_folder + '/gdh.config'
        self.load_settings()
        self.find_git_repo()

    def load_settings(self):
        if os.path.isfile(self.settings_file):
            json_data = open(self.settings_file)
            self.settings = json.load(json_data)
            json_data.close()
        else:
            self.settings = {}

    def find_git_repo(self):
        if not self.settings or not 'git_repo_path' in self.settings:
            folder = self.main_folder
        else:
            folder = self.settings['git_repo_path']

        if '.git' in os.listdir(folder):
            self.settings['git_repo_path'] = folder
            self.prompt_for_commit_id()
        else:
            self.window.show_input_panel("Git repository not found, enter path of your git repository:", self.main_folder + '/', self.set_git_repo, None, None)

    def set_git_repo(self, git_repo):
        self.settings['git_repo_path'] = git_repo
        self.save_settings()
        self.run()

    def save_settings(self):
        settings_file = open(self.settings_file, 'w')
        settings_file.write(json.dumps(self.settings, indent=4, separators=(',', ': ')))
        settings_file.close()

    def prompt_for_commit_id(self):
        clipboard = '' if len(sublime.get_clipboard()) != 40 else sublime.get_clipboard()
        self.window.show_input_panel("Git commit ID:", clipboard, self.retrieve_files, None, None)

    def retrieve_files(self, commitid):
        try:
            repo = git.Repo(self.settings['git_repo_path'])
            active_branch = repo.active_branch
            last_commit = repo.commits(start=active_branch, max_count=1)[0]
            if not commitid:
                commitid = last_commit.id
            selected_commit = repo.commit(commitid)
        except Exception, e:
            print e
            sublime.error_message('Error while fetching commits !')
            return False


        diffs = last_commit.diff(repo, commitid, last_commit.id)
        for selected_diff in selected_commit.diffs:
            diffs.append(selected_diff)

        file_list = []
        for diff in diffs:
            filename = self.settings['git_repo_path'] + '/' + diff.a_path
            if filename not in file_list:
                file_list.append(filename)
        self.file_list = file_list

        panel_name = 'guh_panel'
        self.guh_output_view = self.window.get_output_panel(panel_name)
        v = self.guh_output_view
        v.set_read_only(False)
        edit = v.begin_edit()
        v.insert(edit, v.size(), 'List of modified files from '+commitid+' to '+last_commit.id+' on '+active_branch+':\n')
        for filename in self.file_list:
            v.insert(edit, v.size(), filename + '\n')

        v.end_edit(edit)
        v.show(v.size())
        v.set_read_only(True)

        self.window.run_command("show_panel", {"panel": "output." + panel_name})

        if len(self.file_list) > 10:
            self.comfirm_action()
        else:
            self.open_files(0)

    def comfirm_action(self):
        self.window.show_quick_panel(['Yes open '+str(len(self.file_list))+' files','No do nothing'], self.open_files)

    def open_files(self, arg):
        if arg == 0:
            for filename in self.file_list:
                self.window.open_file(filename)

