import os
from nipype.interfaces.base import CommandLine, CommandLineInputSpec, TraitedSpec, File, traits, isdefined, Directory
from nipype.utils.filemanip import split_filename

'''
sct_maths
sct_propseg
sct_deepseg_sc
sct_create_mask
sct_dmri_moco
sct_dmri_compute_dti
sct_label_vertebrae
sct_register_multimodal
sct_compute_mtr
sct_label_utils
sct_register_to_template
sct_warp_template
sct_extract_metric
sct_process_segmentation
'''

class MeanInputSpec(CommandLineInputSpec):
    input_image = File(exists=True, desc='Input spine image', argstr='-i %s', mandatory=True)
    dimesion = traits.Enum('t','x','y','dwi', desc='Dimension to take mean over', argstr='-mean %s', mandatory=True)
    output_file = File(desc='output filename', argstr='-o %s')


class MeanOutputSpec(TraitedSpec):
    mean_image = File(exists=True, desc='hard segmentation')


class Mean(CommandLine):
    input_spec = MeanInputSpec
    output_spec = MeanOutputSpec
    _cmd = 'sct_maths'

    def _list_outputs(self):
        outputs = self._outputs().get()
        outfile = split_filename(self.inputs.input_image)[1] + '_seg.nii.gz'
        if isdefined(self.inputs.output_directory):
            outputs['spine_segmentation'] = os.path.abspath(os.path.join(self.inputs.output_directory, outfile))
        else:
            outputs['spine_segmentation'] = os.path.abspath(outfile)
        return outputs


#sct_label_vertebrae -i t2.nii -s t2_seg.nii -c t2 -qc ~/qc_singleSubj
class ProcessSegInputSpec(CommandLineInputSpec):
    input_image = File(exists=True, desc='Input spine image', argstr='-i %s', mandatory=True)
    slices = traits.Str(desc='Slice range of the form start:end', argstr='-z %s')
    per_slice = traits.Range(0, 1, desc='1 if per slice metrics should be computed, 0 otherwise', argstr='-perslice %d')
    output_filename = traits.Str(desc='Output filename', argstr='-o %s')


class ProcessSegOutputSpec(TraitedSpec):
    output_csv = File(exists=True, desc='Output CSV')


class ProcessSeg(CommandLine):
    input_spec = ProcessSegInputSpec
    output_spec = ProcessSegOutputSpec
    _cmd = 'sct_process_segmentation'

    def _list_outputs(self):
        outputs = self._outputs().get()
        if isdefined(self.inputs.output_filename):
            outputs['output_csv'] = os.path.abspath(self.inputs.output_filename)
        else:
            outputs['output_csv'] = os.path.abspath('csa.csv')
        return outputs