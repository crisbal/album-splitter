# Some utils for ffmpeg

import os
import math
import subprocess as sbp
from shutil import which

def is_tool(name):
    return which(name) is not None

def get_length(input_media_file):
    if not is_tool('ffprobe'):
        print("ffprobe can't be found!! Returning 0")
        return

    result = sbp.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-i', os.path.realpath(input_media_file)])
    duration_str = result.decode('utf-8').replace('[FORMAT]','').replace('[/FORMAT]','').replace('duration=','').strip()
    # print("result decoded utf8:",result.decode('utf-8').replace('[FORMAT]','').replace('[/FORMAT]','').replace('duration=','').strip())
    duration = float(duration_str)
    return duration

def is_same_length(media_file_A, media_file_B):
    if not os.path.exists(media_file_A) or not os.path.exists(media_file_B):
        raise ValueError("One of input files doesn't exist!!")

    dur_A = get_length(media_file_A)
    dur_B = get_length(media_file_B)

    return math.isclose(dur_A, dur_B, rel_tol=0.03)


class ffmpeg_utils(object):
    def __init__(self, input_file='', output_file='', params_str=''):
        if not is_tool('ffmpeg'):
            raise ValueError("FFMpeg executable was not found!!")

        self.ffmpeg_path = os.path.realpath(which('ffmpeg'))
        self.global_options = '-y -hide_banner -loglevel error'
        self.parameters = []
        self.parameters_as_string = params_str
        self.input_file = '"{}"'.format(os.path.realpath(input_file))
        self.output_file = '"{}"'.format(os.path.realpath(output_file))
        self.cmd_line = ''

    def write_cmd(self, params_str=''):
        self.cmd_line = ' '.join([
            self.ffmpeg_path,
            self.global_options,
            '-i', self.input_file,
            self.parameters_as_string,
            params_str,
            self.output_file])

    def set_input_file(self, input_file_path):
        self.input_file = '"{}"'.format(os.path.realpath(input_file_path))

    def set_output_file(self, output_file_path):
        self.output_file = '"{}"'.format(os.path.realpath(output_file_path))

    def set_params_str(self, param_str):
        self.parameters_as_string = param_str

    def set_params(self, **kwargs):
        params = list(kwargs.keys())
        param_collection = []
        for p in params:
            param_collection.append('-{} {}'.format(p, str(kwargs[p])))
        self.parameters_as_string = ' '.join(param_collection)

    def set_global_options_str(self, opts_str):
        self.global_options = opts_str

    def run(self, params_str=''):
        self.write_cmd(params_str)
        sbp.call(self.cmd_line, shell=True)

    def check_codec(self, codec_name):
        cmd = '{} -loglevel error -codecs'.format(self.ffmpeg_path)
        output = sbp.check_output(cmd)
        if codec_name.lower() in str(output):
            return True
        else:
            return False

    def path(self):
        return self.ffmpeg_path
