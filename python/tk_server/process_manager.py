# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import sys
import os
import subprocess

from PySide import QtGui
from sgtk_file_dialog import SGTKFileDialog

class ProcessManager:
    """
    OS Interface for Shotgun Commands.
    """
    def _get_toolkit_script_name(self):
        return "shotgun"

    def _get_toolkit_fallback_script_name(self):
        return "tank"

    def _get_launcher(self):
        """
        Get Launcher file name from environement.

        :return: String Default Launcher filename. None if none was found,
        """
        return os.environ.get("SHOTGUN_PLUGIN_LAUNCHER")

    def _verify_file_open(self, filepath):
        """
        Common File Open verifications.

        Will raise on errors

        :param filepath: String file path that should be opened.
        """

        if not os.path.isfile(filepath):
            raise Exception("Error opening file [%s]. File not found." % filepath)

    def _get_full_toolkit_path(self, pipeline_config_path):
        """
        Get the full path of the toolkit script.

        :param pipeline_config_path: String Pipeline folder
        :return: String File path of toolkit script (eg: c:/temp/tank)
        """
        exec_script = pipeline_config_path + "/" + self._get_toolkit_script_name()

        if not os.path.isfile(exec_script):
            exec_script = pipeline_config_path + "/" + self._get_toolkit_fallback_script_name()

        return exec_script

    def _verify_toolkit_arguments(self, pipeline_config_path, command):
        """
        Verify that the arguments provided to the toolkit command are valid.

        Will throw on invalid toolkit command arguments.

        :param pipeline_config_path: String Pipeline configuration path
        :param command: Toolkit command to run
        """

        if not command.startswith("shotgun"):
            raise Exception("ExecuteTankCommand error. Command needs to be a shotgun command.")

        if not os.path.isdir(pipeline_config_path):
            raise Exception("Could not find the Pipeline Configuration on disk: " + pipeline_config_path)

        exec_script = self._get_full_toolkit_path(pipeline_config_path)
        if not os.path.isfile(exec_script):
            raise Exception("Could not find the Toolkit command on disk: " + exec_script)

    def _launch_process(self, args, message_error="Error executing command."):
        """
        Standard way of starting a process and handling errors.

        Note: Using Popen instead of call for asynchronous behavior
        :params args: List of elements to pass Popen.
        :params message_error: String to prefix error message in case of an error.
            """

        child = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = child.communicate()
        return_code = child.returncode
        has_error = return_code != 0

        if has_error:
            raise Exception("{message_error}\nCommand: {command}\nReturn code: {return_code}\nOutput: {std_out}\nError: {std_err}".format(message_error=message_error, command=args, return_code=return_code, std_out=out, std_err=err))

        return True

    def open(self, filepath):
        raise NotImplementedError("Open not implemented in base class!")

    def execute_toolkit_command(self, pipeline_config_path, command, args, callback=None):
        """
        Execute Toolkit Command

        :param pipeline_config_path: String Pipeline configuration path
        :param command: Commands
        :param args: List Script arguments
        """

        try:
            self._verify_toolkit_arguments(pipeline_config_path, command)

            #
            # Get toolkit Script Path
            exec_script = self._get_full_toolkit_path(pipeline_config_path)

            # Get toolkit script argument list
            script_args = [command] + args

            #
            # Launch script
            exec_command = [exec_script] + script_args
            sp = subprocess.Popen(exec_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = sp.communicate()

            if callback:
                callback(out, err, sp.returncode)
        except Exception, e:
            raise Exception("Error executing toolkit command: " + e.message)

    def pick_file_or_directory(self, multi=False):
        """
        Pop-up a file selection window.

        Note: Currently haven't been able to get the proper native dialog to multi select
              both file and directories. Using this work-around for now.

        :param multi: Boolean Allow selecting multiple elements.
        :returns: List of files that were selected with file browser.
        """

        # If running outside of desktop, create a Qt App.
        if not QtGui.QApplication.instance():
            app = QtGui.QApplication([])

        dialog = SGTKFileDialog(multi, None)
        dialog.setResolveSymlinks(False)

        # Get result.
        result = dialog.exec_()

        files = []
        if result:
            files = dialog.selectedFiles()

            for f in files:
                if os.path.isdir(f):
                    f += "/"

        return files

    @staticmethod
    def create():
        """
        Create Process Manager according to current context (such as os, etc..)

        :return: ProcessManager
        """

        if sys.platform.startswith("darwin"):
            from process_manager_mac import ProcessManagerMac

            return ProcessManagerMac()
        elif os.name == "nt":
            from process_manager_win import ProcessManagerWin
            return ProcessManagerWin()
        elif os.name == "posix":
            from process_manager_linux import ProcessManagerLinux
            return ProcessManagerLinux()
