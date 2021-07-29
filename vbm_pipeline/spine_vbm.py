import os, glob  # system functions

import nipype.interfaces.io as nio
import nipype.interfaces.fsl as fsl
import nipype.pipeline.engine as pe
import nipype.interfaces.utility as util
import nipype.interfaces.base as base


class GenerateTemplateInputSpec(base.BaseInterfaceInputSpec):
    input_file = base.File(exists=True, desc='input image', mandatory=True)
    flip_axis = base.traits.Int(0, desc='Axis number to flip (-1 to not flip)', usedefault=True)
    output_name = base.traits.Str(desc='Filename for output template')


class GenerateTemplateOutputSpec(base.TraitedSpec):
    template_file = base.File(exists=True, desc='output template')


class GenerateTemplate(base.BaseInterface):
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
        if base.isdefined(self.inputs.output_name):
            output_name = self.inputs.output_name + '.nii.gz'
        else:
            output_name = 'template.nii.gz'
        template_obj.to_filename(output_name)

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        if base.isdefined(self.inputs.output_name):
            outputs['template_file'] = os.path.abspath(self.inputs.output_name + '.nii.gz')
        else:
            outputs['template_file'] = os.path.abspath('template.nii.gz')
        return outputs


def create_spine_template_workflow(output_root):
    wf = pe.Workflow(name='spine_template', base_dir=os.path.join(output_root, 'spine_template'))

    input_node = pe.Node(
        interface=util.IdentityInterface(fields=['spine_files', 'seg_files', 'init_template', 'design_mat', 'tcon']),
        name='input_node')

    # TODO: Add automatic selection of initial template
    #num_dataset = len(input_node.inputs.spine_files)
    #pick_first = pe.Node(util.Split(), 'pick_first')
    #pick_first.inputs.splits = [1, num_dataset-1]
    #wf.connect(input_node, 'spine_files', )

    rigid_registration = pe.MapNode(interface=fsl.FLIRT(), iterfield=['in_file'], name='rigid_registration')
    rigid_registration.inputs.cost = 'normcorr'
    rigid_registration.inputs.cost_func = 'normcorr'
    rigid_registration.inputs.dof = 6
    rigid_registration.inputs.no_search = True
    wf.connect(input_node, 'spine_files', rigid_registration, 'in_file')
    wf.connect(input_node, 'init_template', rigid_registration, 'reference')

    affine_registration = pe.MapNode(interface=fsl.FLIRT(), iterfield=['in_file', 'in_matrix_file'], name='affine_registration')
    affine_registration.inputs.cost = 'normcorr'
    affine_registration.inputs.cost_func = 'normcorr'
    affine_registration.inputs.dof = 12
    wf.connect(input_node, 'spine_files', affine_registration, 'in_file')
    wf.connect(rigid_registration, 'out_matrix_file', affine_registration, 'in_matrix_file')
    wf.connect(input_node, 'init_template', affine_registration, 'reference')

    affine_4d_template = pe.Node(interface=fsl.Merge(),
                                 name='affine_4D_template')
    affine_4d_template.inputs.dimension = 't'
    wf.connect(affine_registration, 'out_file', affine_4d_template, 'in_files')

    affine_template = pe.Node(interface=GenerateTemplate(),
                              name='affine_template')
    wf.connect(affine_4d_template, 'merged_file', affine_template, 'input_file')

    affine_seg_transform = pe.MapNode(interface=fsl.ApplyXFM(), name='affine_seg_transform')
    affine_seg_transform.inputs.apply_xfm = True
    wf.connect(input_node, 'seg_files', affine_seg_transform, 'in_file')
    wf.connect(affine_registration, 'out_matrix_file', affine_seg_transform, 'in_matrix_file')
    wf.connect(input_node, 'init_template', affine_seg_transform, 'reference')

    affine_seg_4d_template = pe.Node(interface=fsl.Merge(),
                                 name='affine_seg_4d_template')
    affine_seg_4d_template.inputs.dimension = 't'
    wf.connect(affine_seg_transform, 'out_file', affine_seg_4d_template, 'in_files')

    affine_seg_template = pe.Node(interface=GenerateTemplate(),
                              name='affine_seg_template')
    wf.connect(affine_seg_4d_template, 'merged_file', affine_seg_template, 'input_file')

    nonlinear_registration = pe.MapNode(interface=fsl.FNIRT(), iterfield=['in_file', 'affine_file'], name='nonlinear_registration')
    nonlinear_registration.inputs.fieldcoeff_file = True
    wf.connect(input_node, 'seg_files', nonlinear_registration, 'in_file')
    wf.connect(affine_registration, 'out_matrix_file', nonlinear_registration, 'affine_file')
    wf.connect(affine_template, 'template_file', nonlinear_registration, 'ref_file')

    nonlinear_4d_template = pe.Node(interface=fsl.Merge(),
                                 name='nonlinear_4d_template')
    nonlinear_4d_template.inputs.dimension = 't'
    wf.connect(nonlinear_registration, 'warped_file', nonlinear_4d_template, 'in_files')

    nonlinear_template = pe.Node(interface=GenerateTemplate(),
                              name='nonlinear_template')
    wf.connect(nonlinear_4d_template, 'merged_file', nonlinear_template, 'input_file')

    nonlinear_seg_transform = pe.MapNode(interface=fsl.ApplyWarp(), iterfield=['in_file', 'field_file'], name='nonlinear_seg_transform')
    wf.connect(input_node, 'seg_files', nonlinear_seg_transform, 'in_file')
    wf.connect(nonlinear_registration, 'out_matrix_file', nonlinear_seg_transform, 'field_file')
    wf.connect(affine_template, 'template_file', nonlinear_seg_transform, 'ref_file')

    nonlinear_seg_4d_template = pe.Node(interface=fsl.Merge(),
                                    name='nonlinear_seg_4d_template')
    nonlinear_seg_4d_template.inputs.dimension = 't'
    wf.connect(nonlinear_seg_transform, 'out_file', nonlinear_seg_4d_template, 'in_files')

    nonlinear_seg_template = pe.Node(interface=GenerateTemplate(),
                                 name='nonlinear_seg_template')
    wf.connect(nonlinear_seg_4d_template, 'merged_file', nonlinear_seg_template, 'input_file')

    # Split here into a separate workflow
    final_registration = pe.MapNode(interface=fsl.FNIRT(), iterfield=['in_file', 'affine_file'],
                                        name='nonlinear_registration')
    final_registration.inputs.fieldcoeff_file = True
    final_registration.inputs.jacobian_file = True
    wf.connect(input_node, 'seg_files', final_registration, 'in_file')
    wf.connect(affine_registration, 'out_matrix_file', final_registration, 'affine_file')
    wf.connect(nonlinear_template, 'template_file', final_registration, 'ref_file')

    final_seg_transform = pe.MapNode(interface=fsl.ApplyWarp(), iterfield=['in_file', 'field_file'],
                                         name='final_seg_transform')
    wf.connect(input_node, 'seg_files', final_seg_transform, 'in_file')
    wf.connect(final_registration, 'out_matrix_file', final_seg_transform, 'field_file')
    wf.connect(nonlinear_template, 'template_file', final_seg_transform, 'ref_file')

    spine_mul_jac = pe.MapNode(interface=fsl.ImageMaths(), iterfield=['in_file', 'in_file2'], name='spine_mul_jac')
    spine_mul_jac.inputs.op_string = '-mul'
    wf.connect(final_registration, 'jacobian_file', spine_mul_jac, 'in_file')
    wf.connect(final_seg_transform, 'out_file', spine_mul_jac, 'in_file2')

    spine_merge = pe.Node(interface=fsl.Merge(),
                       name='spine_merge')
    spine_merge.inputs.dimension = 't'
    wf.connect(final_seg_transform, 'warped_file', spine_merge, 'in_files')

    spine_mod_merge = pe.Node(interface=fsl.Merge(),
                           name='spine_mod_merge')
    spine_mod_merge.inputs.dimension = 't'
    wf.connect(spine_mul_jac, 'out_file', spine_mod_merge, 'in_files')

    spine_mask = pe.Node(interface=fsl.ImageMaths(), name='spine_mask')
    spine_mask.inputs.op_string = '-Tmean -thr 0.01 -bin'
    spine_mask.inputs.out_data_type = 'char'
    wf.connect(spine_merge, 'merged_file', spine_mask, 'in_file')

    gaussian_filter = pe.Node(interface=fsl.ImageMaths(), name='gaussian')
    gaussian_filter.inputs.op_string = '-s 1'
    wf.connect(spine_mod_merge, 'merged_file', gaussian_filter, 'in_file')

    init_randomise = pe.Node(interface=fsl.model.Randomise(), name='randomise')
    init_randomise.inputs.base_name = 'GM_mod_merg_s1'

    wf.connect(gaussian_filter, 'out_file', init_randomise, 'in_file')
    wf.connect(spine_mask, 'out_file', init_randomise, 'mask')
    wf.connect(gaussian_filter, 'design_mat', init_randomise, 'design_mat')
    wf.connect(gaussian_filter, 'tcon', init_randomise, 'tcon')

    return wf

# def create_spine_vbm_workflow(output_root):
#    wf = pe.Workflow(name='spine_vbm', base_dir=os.path.join(output_root, 'spine_vbm'))

    #input_node = pe.Node(
    #    interface=util.IdentityInterface(fields=['spine_files', 'seg_files', 'template', 'design_mat', 'tcon']),
    #    name='input_node')



    #Nonlinear registration to template

    #Update

    #Final registration to template



