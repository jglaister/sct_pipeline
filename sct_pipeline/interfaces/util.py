import os
from nipype.interfaces.base import BaseInterface, BaseInterfaceInputSpec, CommandLine, CommandLineInputSpec, TraitedSpec, File, traits, isdefined, Directory
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

class GenerateTemplateInputSpec(BaseInterfaceInputSpec):
    input_file = File(exists=True, desc='input image', mandatory=True)
    flip_axis = traits.Int(0, desc='Axis number to flip (-1 to not flip)', usedefault=True)
    output_name = traits.Str(desc='Filename for output template')


class GenerateTemplateOutputSpec(TraitedSpec):
    template_file = File(exists=True, desc='output template')


class GenerateTemplate(BaseInterface):
    input_spec = GenerateTemplateInputSpec
    output_spec = GenerateTemplateOutputSpec

    def _run_interface(self, runtime):
        import nibabel as nib
        import numpy as np

        vol_obj = nib.load(self.inputs.input_file)
        vol_data = vol_obj.get_fdata()

        if self.inputs.flip_axis == -1:
            template_data = np.average(vol_data, axis=-1)
        else:
            template_data = (np.average(vol_data, axis=-1) + np.average(np.flip(vol_data, axis=self.inputs.flip_axis), axis=-1)) / 2

        template_obj = nib.Nifti1Image(template_data, vol_obj.affine, vol_obj.header)
        if isdefined(self.inputs.output_name):
            output_name = self.inputs.output_name + '.nii.gz'
        else:
            output_name = 'template.nii.gz'
        template_obj.to_filename(output_name)

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        if isdefined(self.inputs.output_name):
            outputs['template_file'] = os.path.abspath(self.inputs.output_name + '.nii.gz')
        else:
            outputs['template_file'] = os.path.abspath('template.nii.gz')
        return outputs

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