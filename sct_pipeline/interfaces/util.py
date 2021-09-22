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
    dimension = traits.Enum('t','x','y','dwi', desc='Dimension to take mean over', argstr='-mean %s', mandatory=True)
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


class LabelUtilsInputSpec(CommandLineInputSpec):
    input_image = File(exists=True, desc='Input spine image', argstr='-i %s', mandatory=True)
    create_seg_mid = traits.Int(desc='Dimension to take mean over', argstr='-create-seg-mid %s')
    output_file = File(desc='output filename', argstr='-o %s')


class LabelUtilsOutputSpec(TraitedSpec):
    label_image = File(exists=True, desc='hard segmentation')


class LabelUtils(CommandLine):
    input_spec = LabelUtilsInputSpec
    output_spec = LabelUtilsOutputSpec
    _cmd = 'sct_label_utils'

    def _list_outputs(self):
        outputs = self._outputs().get()
        if isdefined(self.inputs.output_file):
            outputs['label_image'] = os.path.abspath(self.inputs.output_file)
        else:
            outputs['label_image'] = os.path.abspath('labels.nii.gz')
        return outputs


class ProcessSegInputSpec(CommandLineInputSpec):
    input_image = File(exists=True, desc='Input spine image', argstr='-i %s', mandatory=True)
    slices = traits.Str(desc='Slice range of the form start:end', argstr='-z %s')
    per_slice = traits.Enum(0, 1, desc='1 if per slice metrics should be computed, 0 otherwise', argstr='-perslice %d')
    output_filename = traits.Str(desc='Output filename', argstr='-o %s')
    vertebrae = traits.Str(desc='Output filename', argstr='-vert %s')
    vertebrae_image = File(exists=True, desc='Input spine image', argstr='-vertfile %s')


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


class ExtractMetricInputSpec(CommandLineInputSpec):
    input_image = File(exists=True, desc='Input metric image', argstr='-i %s', mandatory=True)
    label_image = File(exists=True, desc='Input metric image', argstr='-f %s')
    slices = traits.Str(desc='Slice range of the form start:end', argstr='-z %s')
    per_slice = traits.Enum(0, 1, desc='1 if per slice metrics should be computed, 0 otherwise', argstr='-perslice %d')
    output_filename = traits.Str(desc='Output filename', argstr='-o %s')
    vertebrae = traits.Str(desc='Output filename', argstr='-vert %s')
    vertebrae_image = File(exists=True, desc='Input metric image', argstr='-vertfile %s', mandatory=True)


class ExtractMetricOutputSpec(TraitedSpec):
    output_csv = File(exists=True, desc='Output CSV')


class ExtractMetric(CommandLine):
    input_spec = ExtractMetricInputSpec
    output_spec = ExtractMetricOutputSpec
    _cmd = 'sct_extract_metric'

    def _list_outputs(self):
        outputs = self._outputs().get()
        if isdefined(self.inputs.output_filename):
            outputs['output_csv'] = os.path.abspath(self.inputs.output_filename)
        else:
            outputs['output_csv'] = os.path.abspath('extract_metric.csv')
        return outputs

#sct_label_vertebrae -i t2.nii -s t2_seg.nii -c t2 -qc ~/qc_singleSubj
class ComputeMTRInputSpec(CommandLineInputSpec):
    mt_on_image = File(exists=True, desc='Input spine image', argstr='-mt1 %s', mandatory=True)
    mt_off_image = File(exists=True, desc='Input spine image', argstr='-mt0 %s', mandatory=True)
    #output_filename = traits.Str(desc='Output filename', argstr='-o %s')


class ComputeMTROutputSpec(TraitedSpec):
    mtr_image = File(exists=True, desc='Output MTR')


class ComputeMTR(CommandLine):
    input_spec = ComputeMTRInputSpec
    output_spec = ComputeMTROutputSpec
    _cmd = 'sct_compute_mtr'

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['mtr_image'] = os.path.abspath('mtr.nii.gz')
        return outputs


class ThresholdLabelsInputSpec(BaseInterfaceInputSpec):
    label_files = traits.List(File(exists=True), desc='Vertebrae label image', mandatory=True)
    threshold = traits.Bool(default_value=False, desc='If true, threshold to a binary mask.')
    num_additional_labels_removed = traits.Int(default_value=0, desc='Number of additional labels to remove. '
                                                                     'If set to 1, this will remove an additional '
                                                                     'label.')


class ThresholdLabelsOutputSpec(TraitedSpec):
    thresholded_label_files = traits.List(File(exists=True), desc='Output labels')


class ThresholdLabels(BaseInterface):
    input_spec = ThresholdLabelsInputSpec
    output_spec = ThresholdLabelsOutputSpec

    def _run_interface(self, runtime):
        import nibabel as nib
        import numpy as np

        vol_list = []
        header_list = []
        affine_list = []
        max_common_label = np.inf

        for f in self.inputs.label_files:
            vol_obj = nib.load(f)
            vol_data = vol_obj.get_fdata()
            vol_list.append(vol_data)
            header_list.append(vol_obj.header)
            affine_list.append(vol_obj.affine)

            max_label = np.max(vol_data)
            if max_label < max_common_label:
                max_common_label = max_label

        max_common_label = max_common_label - self.inputs.num_additional_labels_removed

        for idx, f in enumerate(self.inputs.label_files):
            vol_data = vol_list[idx]
            vol_data[vol_data > max_common_label] = 0
            if self.inputs.threshold is True:
                vol_data[vol_data > 0] = 1
            vol_obj = nib.Nifti1Image(vol_data, affine_list[idx], header_list[idx])

            output_name = split_filename(f)[1] + '_thresh.nii.gz'
            vol_obj.to_filename(output_name)

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['thresholded_label_files'] = [os.path.abspath(split_filename(f)[1] + '_thresh.nii.gz') for f in self.inputs.label_files]

        return outputs