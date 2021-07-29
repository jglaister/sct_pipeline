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

#sct_deepseg_sc
class SCTDeepSegInputSpec(CommandLineInputSpec):
    input_image = File(exists=True, desc='Input spine image', argstr='-i %s', mandatory=True)
    contrast = traits.Enum('t1','t2','t2s','dwi', desc='Input image contrast type', argstr='-c %s', mandatory=True)
    #centerline = traits.Enum('svm','cnn','file', desc='Method to obtain centerline (viewer method disabled)', argstr='-centerline %s')
    #centerline_file = File(exists=True, desc='Input spine image if a file is used to find centerline', argstr='-file_centerline %s')
    threshold = traits.Range(-1.0, 1.0, desc='Threshold (Set to -1 for soft seg)', argstr='-thr %g')
    #kernel = traits.Enum('2d','3d', desc='Kernel (2d or 3d)', argstr='-kernel %s')
    #includes_brain = traits.Range(0, 1, desc='1 if image contains brain, 0 otherwise', argstr='-brain %d')
    output_directory = Directory(desc='output directory', argstr='-ofolder %s')


class SCTDeepSegOutputSpec(TraitedSpec):
    spine_segmentation = File(exists=True, desc='segmentation')


class SCTDeepSeg(CommandLine):
    input_spec = SCTDeepSegInputSpec
    output_spec = SCTDeepSegOutputSpec
    _cmd = 'sct_deepseg_sc'

    def _list_outputs(self):
        outputs = self._outputs().get()
        outfile = split_filename(self.inputs.input_image)[1] + '_seg.nii.gz'
        if isdefined(self.inputs.output_directory):
            outputs['spine_segmentation'] = os.path.abspath(os.path.join(self.inputs.output_directory, outfile))
        else:
            outputs['spine_segmentation'] = os.path.abspath(outfile)
        return outputs


#sct_propseg
class SCTPropSegInputSpec(CommandLineInputSpec):
    input_image = File(exists=True, desc='Input spine image', argstr='-i %s', mandatory=True)
    contrast = traits.Enum('t1','t2','t2s','dwi', desc='Input image contrast type', argstr='-c %s', mandatory=True)
    output_file = File(desc='output filename', argstr='-o %s')


class SCTPropSegOutputSpec(TraitedSpec):
    spine_segmentation = File(exists=True, desc='hard segmentation')


class SCTPropSeg(CommandLine):
    input_spec = SCTDeepSegInputSpec
    output_spec = SCTDeepSegOutputSpec
    _cmd = 'sct_propseg'

    def _list_outputs(self):
        outputs = self._outputs().get()
        outfile = split_filename(self.inputs.input_image)[1] + '_seg.nii.gz'
        if isdefined(self.inputs.output_directory):
            outputs['spine_segmentation'] = os.path.abspath(os.path.join(self.inputs.output_directory, outfile))
        else:
            outputs['spine_segmentation'] = os.path.abspath(outfile)
        return outputs


#sct_maths
class SCTMeanInputSpec(CommandLineInputSpec):
    input_image = File(exists=True, desc='Input spine image', argstr='-i %s', mandatory=True)
    dimesion = traits.Enum('t','x','y','dwi', desc='Dimension to take mean over', argstr='-mean %s', mandatory=True)
    output_file = File(desc='output filename', argstr='-o %s')


class SCTMeanOutputSpec(TraitedSpec):
    mean_image = File(exists=True, desc='hard segmentation')

class SCTMean(CommandLine):
    input_spec = SCTMeanInputSpec
    output_spec = SCTMeanOutputSpec
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
class SCTLabelVertebraeInputSpec(CommandLineInputSpec):
    input_image = File(exists=True, desc='Input spine image', argstr='-i %s', mandatory=True)
    spine_segmentation = File(exists=True, desc='Input spine segmentation image', argstr='-s %s', mandatory=True)
    contrast = traits.Enum('t1','t2', desc='Input image contrast type', argstr='-c %s', mandatory=True)
    initial_label = File(exists=True, desc='Initialize vertebral labeling by providing a nifti file that has a single '
                                           'disc label', argstr='-initlabel %s')
    template_directory = Directory(exists=True, desc='template directory', argstr='-t %s')
    output_directory = Directory(exists=True, desc='output directory', argstr='-ofolder %s')


class SCTLabelVertebraeOutputSpec(TraitedSpec):
    labels = File(exists=True, desc='hard segmentation')


class SCTLabelVertebrae(CommandLine):
    input_spec = SCTDeepSegInputSpec
    output_spec = SCTDeepSegOutputSpec
    _cmd = 'sct_label_vertebrae'

    def _list_outputs(self):
        outputs = self._outputs().get()
        outfile = split_filename(self.inputs.spine_segmentation)[1] + '_labeled.nii.gz'
        if isdefined(self.inputs.output_directory):
            outputs['labels'] = os.path.abspath(os.path.join(self.inputs.output_directory, outfile))
        else:
            outputs['labels'] = os.path.abspath(outfile)
        return outputs


class SCTProcessSegInputSpec(CommandLineInputSpec):
    input_image = File(exists=True, desc='Input spine image', argstr='-i %s', mandatory=True)
    slices = traits.Str(desc='Slice range of the form start:end', argstr='-z %s')
    per_slice = traits.Range(0, 1, desc='1 if per slice metrics should be computed, 0 otherwise', argstr='-perslice %d')
    output_filename = traits.Str(desc='Output filename', argstr='-o %s')


class SCTProcessSegOutputSpec(TraitedSpec):
    output_csv = File(exists=True, desc='Output CSV')


class SCTProcessSeg(CommandLine):
    input_spec = SCTProcessSegInputSpec
    output_spec = SCTProcessSegOutputSpec
    _cmd = 'sct_process_segmentation'

    def _list_outputs(self):
        outputs = self._outputs().get()
        if isdefined(self.inputs.output_filename):
            outputs['output_csv'] = os.path.abspath(self.inputs.output_filename)
        else:
            outputs['output_csv'] = os.path.abspath('csa.csv')
        return outputs

class SCTRegisterToTemplateInputSpec(CommandLineInputSpec):
    input_image = File(exists=True, desc='Input spine image', argstr='-i %s', mandatory=True)
    spine_segmentation = File(exists=True, desc='Input spine segmentation', argstr='-s %s', mandatory=True)
    contrast = traits.Enum('t1', 't2', 't2s', desc='Input image contrast type', argstr='-c %s')
    disc_labels = File(exists=True, desc='Input disc label file', argstr='-ldisc %s', mandatory=True)


class SCTRegisterToTemplateOutputSpec(TraitedSpec):
    output_file = File(exists=True, desc='Output CSV')


class SCTRegisterToTemplate(CommandLine):
    input_spec = SCTRegisterToTemplateInputSpec
    output_spec = SCTRegisterToTemplateOutputSpec
    _cmd = 'sct_process_segmentation'

    def _list_outputs(self):
        outputs = self._outputs().get()
        if isdefined(self.inputs.output_filename):
            outputs['output_file'] = os.path.abspath(self.inputs.output_filename)
        else:
            outputs['output_file'] = os.path.abspath('csa.csv')
        return outputs

