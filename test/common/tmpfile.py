# Copyright 2023 Ericsson AB
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Classes for safe temporary file/directory handling
"""
import logging
import shutil
import tempfile


class TemporaryDir:
    """
    Safely creates and destroys temporary folder
    """

    def __init__(self):
        self._temp_dir = None

    def __enter__(self):
        self._temp_dir = tempfile.mkdtemp()
        logging.debug("Created %s", self._temp_dir)
        return self._temp_dir

    def __exit__(self, tipe, value, traceback):
        shutil.rmtree(self._temp_dir)  # type: ignore
        logging.debug("Removed %s", self._temp_dir)
