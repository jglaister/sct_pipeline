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

class RegisterToTemplateInputSpec(CommandLineInputSpec):
    input_image = File(exists=True, desc='Input spine image', argstr='-i %s', mandatory=True)
    spine_segmentation = File(exists=True, desc='Input spine segmentation', argstr='-s %s', mandatory=True)
    contrast = traits.Enum('t1', 't2', 't2s', desc='Input image contrast type', argstr='-c %s')
    disc_labels = File(exists=True, desc='Input disc label file', argstr='-ldisc %s', mandatory=True)
    reference = traits.Enum('template','subject',argstr='-ref %s')
    param = traits.Str(desc='Parameters', argstr='-param %s')


class RegisterToTemplateOutputSpec(TraitedSpec):
    anat2template = File(exists=True, desc='Output CSV')
    template2anat = File(exists=True, desc='Output CSV')
    warp_anat2template = File(exists=True, desc='Output CSV')
    warp_template2anat = File(exists=True, desc='Output CSV')


class RegisterToTemplate(CommandLine):
    input_spec = RegisterToTemplateInputSpec
    output_spec = RegisterToTemplateOutputSpec
    _cmd = 'sct_register_to_template'

    def _list_outputs(self):
        outputs = self._outputs().get()

        outputs['anat2template'] = os.path.abspath('anat2template.nii.gz')
        outputs['template2anat'] = os.path.abspath('template2anat.nii.gz')
        outputs['warp_anat2template'] = os.path.abspath('warp_anat2template.nii.gz')
        outputs['warp_template2anat'] = os.path.abspath('warp_template2anat.nii.gz')

        return outputs


class WarpTemplateInputSpec(CommandLineInputSpec):
    destination_image = File(exists=True, desc='Input spine image', argstr='-d %s', mandatory=True)
    warping_field = File(exists=True, desc='Input spine segmentation', argstr='-w %s', mandatory=True)
    warp_white_matter = traits.Enum(0, 1, desc='Input image contrast type', argstr='-a %s')
    warp_spinal_levels = traits.Enum(0, 1, desc='Input image contrast type', argstr='-s %s')


class WarpTemplateOutputSpec(TraitedSpec):
    cord = File(exists=True, desc='Output CSV')
    levels = File(exists=True, desc='Output CSV')
    gm = File(exists=True, desc='Output CSV')
    wm = File(exists=True, desc='Output CSV')
    # What other outputs are needed?


class WarpTemplate(CommandLine):
    input_spec = WarpTemplateInputSpec
    output_spec = WarpTemplateOutputSpec
    _cmd = 'sct_warp_template'

    def _list_outputs(self):
        outputs = self._outputs().get()

        outputs['cord'] = os.path.abspath(os.path.join('label','template', 'PAM50_cord.nii.gz'))
        outputs['levels'] = os.path.abspath(os.path.join('label','template', 'PAM50_levels.nii.gz'))
        outputs['gm'] = os.path.abspath(os.path.join('label','template', 'PAM50_gm.nii.gz'))
        outputs['wm'] = os.path.abspath(os.path.join('label','template', 'PAM50_wm.nii.gz'))

        return outputs

class RegisterMultimodalInputSpec(CommandLineInputSpec):
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


class RegisterMultimodalOutputSpec(TraitedSpec):
    warped_input_image = File(exists=True, desc='Output CSV')
    warped_destination_image = File(exists=True, desc='Output CSV')
    warpfield_input_to_destination = File(exists=True, desc='Output CSV')
    warpfield_destination_to_input = File(exists=True, desc='Output CSV')


class RegisterMultimodal(CommandLine):
    input_spec = RegisterMultimodalInputSpec
    output_spec = RegisterMultimodalOutputSpec
    _cmd = 'sct_register_multimodal'

    def _list_outputs(self):
        outputs = self._outputs().get()
        input_image_base = split_filename(self.inputs.input_image)[1]
        destination_image_base = split_filename(self.inputs.destination_image)[1]
        if input_image_base != destination_image_base:
            outputs['warped_input_image'] = os.path.abspath(input_image_base + '_reg.nii.gz')
            outputs['warped_destination_image'] = os.path.abspath(destination_image_base + '_reg.nii.gz')
        else:
            outputs['warped_input_image'] = os.path.abspath(input_image_base + '_src_reg.nii.gz')
            outputs['warped_destination_image'] = os.path.abspath(destination_image_base + '_dest_reg.nii.gz')
        outputs['warpfield_input_to_destination'] = os.path.abspath(
            'warp_' + input_image_base + '2' + destination_image_base + '.nii.gz')
        outputs['warpfield_destination_to_input'] = os.path.abspath(
            'warp_' + destination_image_base + '2' + input_image_base + '.nii.gz')

        return outputs


class GetCenterlineInputSpec(CommandLineInputSpec):
    input_image = File(exists=True, desc='Input spine image', argstr='-i %s', mandatory=True)
    contrast = traits.Enum('t1', 't2', 't2s', 'dwi', desc='Input image contrast type', argstr='-c %s')
    #output_filename = traits.Str(desc='Output filename', argstr='-o %s')


class GetCenterlineOutputSpec(TraitedSpec):
    centerline_file = File(exists=True, desc='Output CSV')

#TODO: Save in correct dir
class GetCenterline(CommandLine):
    input_spec = GetCenterlineInputSpec
    output_spec = GetCenterlineOutputSpec
    _cmd = 'sct_get_centerline'

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['centerline_file'] = os.path.abspath(split_filename(self.inputs.input_image)[1] + '_centerline.nii.gz')
        #split_filename(self.inputs.spine_segmentation)[1] + '_labeled.nii.gz'
        return outputs


class StraightenSpinalcordInputSpec(CommandLineInputSpec):
    input_image = File(exists=True, desc='Input spine image', argstr='-i %s', mandatory=True)
    segmentation_image = File(exists=True, desc='Input spine image', argstr='-s %s', mandatory=True)


class StraightenSpinalcordOutputSpec(TraitedSpec):
    straightened_input = File(exists=True, desc='Output CSV')
    warp_curve2straight = File(exists=True, desc='Output CSV')
    warp_straight2curve = File(exists=True, desc='Output CSV')


class StraightenSpinalcord(CommandLine):
    input_spec = StraightenSpinalcordInputSpec
    output_spec = StraightenSpinalcordOutputSpec
    _cmd = 'sct_straighten_spinalcord'

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['straightened_input'] = os.path.abspath(split_filename(self.inputs.input_image)[1] + '_straight.nii.gz')
        outputs['warp_curve2straight'] = os.path.abspath('warp_curve2straight.nii.gz')
        outputs['warp_straight2curve'] = os.path.abspath('warp_straight2curve.nii.gz')
        #split_filename(self.inputs.spine_segmentation)[1] + '_labeled.nii.gz'
        return outputs

class ApplyTransformInputSpec(CommandLineInputSpec):
    input_image = File(exists=True, desc='Input spine image', argstr='-i %s', mandatory=True)
    destination_image = File(exists=True, desc='Input spine image', argstr='-d %s', mandatory=True)
    transforms = File(exists=True, desc='Input spine image', argstr='-w %s', mandatory=True)
    interpolation = traits.Enum('spline', 'linear', 'nn', 'label', desc='Input image contrast type', argstr='-x %s')

class ApplyTransformOutputSpec(TraitedSpec):
    output_file = File(exists=True, desc='Output CSV')

class ApplyTransform(CommandLine):
    input_spec = ApplyTransformInputSpec
    output_spec = ApplyTransformOutputSpec
    _cmd = 'sct_apply_transfo'

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['output_file'] = os.path.abspath(split_filename(self.inputs.input_image)[1] + '_reg.nii.gz')
        #split_filename(self.inputs.spine_segmentation)[1] + '_labeled.nii.gz'
        return outputs
