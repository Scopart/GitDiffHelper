import sublime, sublime_plugin
import git
import os, json

class GitDiffHelperCommand(sublime_plugin.WindowCommand):

    guh_output_view = None
    file_list = None
    git_repo = None
    settings = None
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
            self.git_repo = self.settings['git_repo_path']

    def find_git_repo(self):
        if not self.git_repo:
            folder = self.main_folder
        else:
            folder = self.git_repo

        if '.git' in os.listdir(folder):
            self.git_repo = folder
            self.prompt_for_commit_id()
        else:
            self.window.show_input_panel("Git repository not found, enter your root git repository:", self.main_folder + '/', self.save_settings, None, None)

    def save_settings(self, git_repo):
        settings_file = open(self.settings_file, 'w')
        settings_file.write(json.dumps({'git_repo_path':git_repo}, indent=4, separators=(',', ': ')))
        settings_file.close()
        self.run()

    def prompt_for_commit_id(self):
        clipboard = '' if len(sublime.get_clipboard()) != 40 else sublime.get_clipboard()
        self.window.show_input_panel("Git commit ID:", clipboard, self.retrieve_files, None, None)

    def retrieve_files(self, commitid):
        try:
            repo = git.Repo(self.git_repo)
            active_branch = repo.active_branch
            last_commit = repo.commits(start=active_branch, max_count=1)[0]
        except Exception, e:
            print e
            sublime.error_message('Error while fetching commits !')
            return False

        if not commitid:
            commitid = last_commit.id
        selected_commit = repo.commit(commitid)

        diffs = last_commit.diff(repo, commitid, last_commit.id)
        for selected_diff in selected_commit.diffs:
            diffs.append(selected_diff)

        file_list = []
        for diff in diffs:
            filename = self.git_repo + '/' + diff.a_path
            if filename not in file_list:
                file_list.append(filename)
        self.file_list = file_list

        if len(self.file_list) > 10:
            self.comfirm_action()
        else:
            self.open_files(0)

    def comfirm_action(self):
        panel_name = 'guh_panel'
        self.guh_output_view = self.window.get_output_panel(panel_name)
        v = self.guh_output_view

        v.set_read_only(False)
        edit = v.begin_edit()
        for filename in self.file_list:
            v.insert(edit, v.size(), filename + '\n')

        v.insert(edit, v.size(), str(len(self.file_list)) + ' files to open, are you sure ? (confirm in quick panel)' + '\n')
        v.end_edit(edit)
        v.show(v.size())
        v.set_read_only(True)

        self.window.run_command("show_panel", {"panel": "output." + panel_name})
        self.window.show_quick_panel(['Yes open '+str(len(self.file_list))+' files','No do nothing'], self.open_files)

    def open_files(self, arg):
        if arg == 0:
            for filename in self.file_list:
                self.window.open_file(filename)

