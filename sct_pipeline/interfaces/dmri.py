import os
from nipype.interfaces.base import CommandLine, CommandLineInputSpec, TraitedSpec, File, traits, isdefined, Directory
from nipype.utils.filemanip import split_filename

class MotionCorrectionInputSpec(CommandLineInputSpec):
    dwi_image = File(exists=True, desc='Input spine image', argstr='-i %s', mandatory=True)
    bvec = File(exists=True, desc='Input spine image', argstr='-bvec %s', mandatory=True)
    bval = File(exists=True, desc='Input spine image', argstr='-bval %s')

    mask = File(exists=True, desc='Input spine segmentation image', argstr='-m %s')
    bvalmin = traits.Float(desc='Minimum b-value', argstr='-bvalmin %s')
    interpolation = traits.Enum('spline','nn', 'linear', desc='Input image contrast type', argstr='-x %s')
    output_directory = Directory(exists=True, desc='output directory', argstr='-ofolder %s')


class MotionCorrectionOutputSpec(TraitedSpec):
    moco_dwi = File(exists=True, desc='hard segmentation')
    mean_moco_dwi = File(exists=True, desc='hard segmentation')


class MotionCorrection(CommandLine):
    input_spec = MotionCorrectionInputSpec
    output_spec = MotionCorrectionOutputSpec
    _cmd = 'sct_dmri_moco'

    def _list_outputs(self):
        outputs = self._outputs().get()
        outfile = split_filename(self.inputs.spine_segmentation)[1] + '_moco.nii.gz'
        meanfile = split_filename(self.inputs.spine_segmentation)[1] + '_moco_dwi_mean.nii.gz'
        if isdefined(self.inputs.output_directory):
            outputs['moco_dwi'] = os.path.abspath(os.path.join(self.inputs.output_directory, outfile))
            outputs['mean_moco_dwi'] = os.path.abspath(os.path.join(self.inputs.output_directory, meanfile))
        else:
            outputs['moco_dwi'] = os.path.abspath(outfile)
            outputs['mean_moco_dwi'] = os.path.abspath(meanfile)
        return outputs

class ComputeDTIInputSpec(CommandLineInputSpec):
    dwi_image = File(exists=True, desc='Input spine image', argstr='-i %s', mandatory=True)
    bvec = File(exists=True, desc='Input spine image', argstr='-bvec %s', mandatory=True)
    bval = File(exists=True, desc='Input spine image', argstr='-bval %s', mandatory=True)

    mask = File(exists=True, desc='Input spine segmentation image', argstr='-m %s')
    method = traits.Enum('standard','restore', desc='DTI estimation method to use', argstr='-method %s')
    eigenvalue = traits.Enum('0','1', desc='1 if eigenvalues and eigenvectors should be output', argstr='-evecs %s')
    output_prefix = traits.Str(desc='Output filename', argstr='-o %s')


class ComputeDTIOutputSpec(TraitedSpec):
    fa = File(exists=True, desc='hard segmentation')
    md = File(exists=True, desc='hard segmentation')
    rd = File(exists=True, desc='hard segmentation')


class ComputeDTI(CommandLine):
    input_spec = MotionCorrectionInputSpec
    output_spec = MotionCorrectionOutputSpec
    _cmd = 'sct_dmri_compute_dti'

    def _list_outputs(self):
        outputs = self._outputs().get()
        outfile = split_filename(self.inputs.spine_segmentation)[1] + '_moco.nii.gz'
        meanfile = split_filename(self.inputs.spine_segmentation)[1] + '_moco_dwi_mean.nii.gz'
        if isdefined(self.inputs.output_directory):
            outputs['moco_dwi'] = os.path.abspath(os.path.join(self.inputs.output_directory, outfile))
            outputs['mean_moco_dwi'] = os.path.abspath(os.path.join(self.inputs.output_directory, meanfile))
        else:
            outputs['moco_dwi'] = os.path.abspath(outfile)
            outputs['mean_moco_dwi'] = os.path.abspath(meanfile)
        return outputs