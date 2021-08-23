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
    input_spec = SCTLabelVertebraeInputSpec
    output_spec = SCTLabelVertebraeOutputSpec
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


class SCTRegisterMultimodalInputSpec(CommandLineInputSpec):
    input_image = File(exists=True, desc='Input spine image', argstr='-i %s', mandatory=True)
    destination_image = File(exists=True, desc='Input spine image', argstr='-d %s', mandatory=True)
    input_segmentation = File(exists=True, desc='Input spine segmentation', argstr='-iseg %s')
    destination_segmentation = File(exists=True, desc='Input spine segmentation', argstr='-dseg %s')
    input_label = File(exists=True, desc='Input spine segmentation', argstr='-ilabel %s')
    destination_label = File(exists=True, desc='Input spine segmentation', argstr='-dlabel %s')
    mask = File(exists=True, desc='Input spine segmentation', argstr='-m %s')
    param = traits.Str(desc='Parameters', argstr='-param %s')
    interpolation = traits.Enum('linear', 'nn', 'spline', desc='Input image contrast type', argstr='-x %s')
    #contrast = traits.Enum('t1', 't2', 't2s', desc='Input image contrast type', argstr='-c %s')
    #disc_labels = File(exists=True, desc='Input disc label file', argstr='-ldisc %s', mandatory=True)


class SCTRegisterMultimodalOutputSpec(TraitedSpec):
    output_file = File(exists=True, desc='Output CSV')
    output_warp = File(exists=True, desc='Output CSV')


class SCTRegisterMultimodal(CommandLine):
    input_spec = SCTRegisterMultimodalInputSpec
    output_spec = SCTRegisterMultimodalOutputSpec
    _cmd = 'sct_register_multimodal'

    def _list_outputs(self):
        outputs = self._outputs().get()
        if isdefined(self.inputs.output_filename):
            outputs['output_file'] = os.path.abspath(self.inputs.output_filename)
        else:
            outputs['output_file'] = os.path.abspath('csa.csv')
        return outputs

class SCTGetCenterlineInputSpec(CommandLineInputSpec):
    input_image = File(exists=True, desc='Input spine image', argstr='-i %s', mandatory=True)
    contrast = traits.Enum('t1', 't2', 't2s', 'dwi', desc='Input image contrast type', argstr='-c %s')
    #output_filename = traits.Str(desc='Output filename', argstr='-o %s')

class SCTGetCenterlineOutputSpec(TraitedSpec):
    centerline_file = File(exists=True, desc='Output CSV')

#TODO: Save in correct dir
class SCTGetCenterline(CommandLine):
    input_spec = SCTGetCenterlineInputSpec
    output_spec = SCTGetCenterlineOutputSpec
    _cmd = 'sct_get_centerline'

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['centerline_file'] = os.path.abspath(split_filename(self.inputs.input_image)[1] + '_centerline.nii.gz')
        #split_filename(self.inputs.spine_segmentation)[1] + '_labeled.nii.gz'
        return outputs

class SCTStraightenSpinalcordInputSpec(CommandLineInputSpec):
    input_image = File(exists=True, desc='Input spine image', argstr='-i %s', mandatory=True)
    segmentation_image = File(exists=True, desc='Input spine image', argstr='-s %s', mandatory=True)

class SCTStraightenSpinalcordOutputSpec(TraitedSpec):
    straightened_input = File(exists=True, desc='Output CSV')
    warp_curve2straight = File(exists=True, desc='Output CSV')
    warp_straight2curve = File(exists=True, desc='Output CSV')

class SCTStraightenSpinalcord(CommandLine):
    input_spec = SCTStraightenSpinalcordInputSpec
    output_spec = SCTStraightenSpinalcordOutputSpec
    _cmd = 'sct_straighten_spinalcord'

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['straightened_input'] = os.path.abspath(split_filename(self.inputs.input_image)[1] + '_straight.nii.gz')
        outputs['warp_curve2straight'] = os.path.abspath('warp_curve2straight.nii.gz')
        outputs['warp_straight2curve'] = os.path.abspath('warp_straight2curve.nii.gz')
        #split_filename(self.inputs.spine_segmentation)[1] + '_labeled.nii.gz'
        return outputs

class SCTApplyTransformInputSpec(CommandLineInputSpec):
    input_file = File(exists=True, desc='Input spine image', argstr='-i %s', mandatory=True)
    destination_file = File(exists=True, desc='Input spine image', argstr='-d %s', mandatory=True)
    transforms = File(exists=True, desc='Input spine image', argstr='-w %s', mandatory=True)
    interpolation = traits.Enum('spline', 'linear', 'nn', 'label', desc='Input image contrast type', argstr='-x %s')

class SCTApplyTransformOutputSpec(TraitedSpec):
    output_file = File(exists=True, desc='Output CSV')

class SCTApplyTransform(CommandLine):
    input_spec = SCTApplyTransformInputSpec
    output_spec = SCTApplyTransformOutputSpec
    _cmd = 'sct_apply_transfo'

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['output_file'] = os.path.abspath(split_filename(self.inputs.input_image)[1] + '_straight.nii.gz')
        #split_filename(self.inputs.spine_segmentation)[1] + '_labeled.nii.gz'
        return outputs
