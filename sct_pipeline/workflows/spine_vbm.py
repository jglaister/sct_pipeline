import os  # system functions

import nipype.pipeline.engine as pe
import nipype.interfaces.utility as util
import nipype.interfaces.base as base

import sct_pipeline.interfaces.registration as sct_reg
import sct_pipeline.interfaces.segmentation as sct_seg
import sct_pipeline.interfaces.util as sct_util





def create_spine_template_workflow(output_root, template_index=0):
    # TODO: Split into seperate workflows
    wf = pe.Workflow(name='spine_template', base_dir=os.path.join(output_root, 'spine_template'))

    input_node = pe.Node(
        interface=util.IdentityInterface(fields=['spine_files', 'design_mat', 'tcon']),
        name='input_node')

    spine_segmentation = pe.MapNode(interface=sct_seg.DeepSeg(),
                                    iterfield=['input_image'],
                                    name='spine_segmentation')
    spine_segmentation.inputs.contrast = 't2'
    wf.connect(input_node, 'spine_files', spine_segmentation, 'input_image')

    label_vertebrae = pe.MapNode(interface=sct_seg.LabelVertebrae(),
                                 iterfield=['input_image', 'spine_segmentation'],
                                 name='label_vertebrae')
    label_vertebrae.inputs.contrast = 't2'
    wf.connect(input_node, 'spine_files', label_vertebrae, 'input_image')
    wf.connect(spine_segmentation, 'spine_segmentation', label_vertebrae, 'spine_segmentation')

    # Straighten the spinalcord, then apply the warp field to the segmentation and label maps
    straighten_spinalcord = pe.MapNode(interface=sct_reg.StraightenSpinalcord(),
                                       iterfield=['input_image','segmentation_image'],
                                       name='straighten_spinalcord')
    wf.connect(input_node, 'spine_files', straighten_spinalcord, 'input_image')
    wf.connect(spine_segmentation, 'spine_segmentation', straighten_spinalcord, 'segmentation_image')

    straighten_segmentation = pe.MapNode(interface=sct_reg.ApplyTransform(),
                                         iterfield=['input_image', 'destination_image', 'transforms'],
                                         name='straighten_segmentation')
    straighten_segmentation.inputs.interpolation = 'linear'  # Soft segmentation, so use linear
    wf.connect(spine_segmentation, 'spine_segmentation', straighten_segmentation, 'input_image')
    wf.connect(straighten_spinalcord, 'straightened_input', straighten_segmentation, 'destination_image')
    wf.connect(straighten_spinalcord, 'warp_curve2straight', straighten_segmentation, 'transforms')

    straighten_labels = pe.MapNode(interface=sct_reg.ApplyTransform(),
                                   iterfield=['input_image', 'destination_image', 'transforms'],
                                   name='straighten_labels')
    straighten_labels.inputs.interpolation = 'nn'  # Hard label segmentation, so use nn
    wf.connect(label_vertebrae, 'labels', straighten_labels, 'input_image')
    wf.connect(straighten_spinalcord, 'straightened_input', straighten_labels, 'destination_image')
    wf.connect(straighten_spinalcord, 'warp_curve2straight', straighten_labels, 'transforms')

    # Select the template_index element of the straightened spinalcord to use as the initial template
    select_init_template = pe.Node(interface=util.Select(),
                                   name='select_init_template')
    select_init_template.inputs.index = [template_index]
    wf.connect(straighten_spinalcord, 'straightened_input', select_init_template, 'inlist')

    select_init_label = pe.Node(interface=util.Select(),
                                name='select_init_label')
    select_init_label.inputs.index = [template_index]
    wf.connect(straighten_labels, 'output_file', select_init_label, 'inlist')

    select_init_seg = pe.Node(interface=util.Select(),
                              name='select_init_seg')
    select_init_seg.inputs.index = [template_index]
    wf.connect(straighten_segmentation, 'output_file', select_init_seg, 'inlist')

    # TODO: Split here into a separate workflow
    rigid_registration = pe.MapNode(interface=sct_reg.RegisterMultimodal(),
                                    iterfield=['input_image', 'input_label'],
                                    name='rigid_registration')
    rigid_registration.inputs.param = 'step=0,type=label,algo=rigid:step=1,type=im,algo=affine,metric=CC'
    wf.connect(straighten_spinalcord, 'straightened_input', rigid_registration, 'input_image')
    wf.connect(straighten_labels, 'output_file', rigid_registration, 'input_label')
    wf.connect(select_init_template, 'out', rigid_registration, 'destination_image')
    wf.connect(select_init_label, 'out', rigid_registration, 'destination_label')


    #num_dataset = len(input_node.inputs.spine_files)
    #pick_first = pe.Node(util.Split(), 'pick_first')
    #pick_first.inputs.splits = [1, num_dataset-1]
    #wf.connect(input_node, 'spine_files', )

    # rigid_registration = pe.MapNode(interface=fsl.FLIRT(), iterfield=['in_file'], name='rigid_registration')
    # rigid_registration.inputs.cost = 'normcorr'
    # rigid_registration.inputs.cost_func = 'normcorr'
    # rigid_registration.inputs.dof = 6
    # rigid_registration.inputs.no_search = True
    # wf.connect(input_node, 'spine_files', rigid_registration, 'in_file')
    # wf.connect(input_node, 'init_template', rigid_registration, 'reference')
    #
    # rigid_4d_template = pe.Node(interface=fsl.Merge(),
    #                              name='rigid_4d_template')
    # rigid_4d_template.inputs.dimension = 't'
    # wf.connect(rigid_registration, 'out_file', rigid_4d_template, 'in_files')
    #
    # affine_registration = pe.MapNode(interface=fsl.FLIRT(),
    #                                  iterfield=['in_file', 'in_matrix_file'],
    #                                  name='affine_registration')
    # affine_registration.inputs.cost = 'normcorr'
    # affine_registration.inputs.cost_func = 'normcorr'
    # affine_registration.inputs.dof = 12
    # wf.connect(input_node, 'spine_files', affine_registration, 'in_file')
    # wf.connect(rigid_registration, 'out_matrix_file', affine_registration, 'in_matrix_file')
    # wf.connect(input_node, 'init_template', affine_registration, 'reference')
    #
    # affine_4d_template = pe.Node(interface=fsl.Merge(),
    #                              name='affine_4D_template')
    # affine_4d_template.inputs.dimension = 't'
    # wf.connect(affine_registration, 'out_file', affine_4d_template, 'in_files')
    #
    # affine_template = pe.Node(interface=GenerateTemplate(),
    #                           name='affine_template')
    # wf.connect(affine_4d_template, 'merged_file', affine_template, 'input_file')
    #
    # affine_seg_transform = pe.MapNode(interface=fsl.ApplyXFM(),
    #                                   iterfield=['in_file', 'in_matrix_file'],
    #                                   name='affine_seg_transform')
    # affine_seg_transform.inputs.apply_xfm = True
    # wf.connect(input_node, 'seg_files', affine_seg_transform, 'in_file')
    # wf.connect(affine_registration, 'out_matrix_file', affine_seg_transform, 'in_matrix_file')
    # wf.connect(input_node, 'init_template', affine_seg_transform, 'reference')
    #
    # affine_seg_4d_template = pe.Node(interface=fsl.Merge(),
    #                                  name='affine_seg_4d_template')
    # affine_seg_4d_template.inputs.dimension = 't'
    # wf.connect(affine_seg_transform, 'out_file', affine_seg_4d_template, 'in_files')
    #
    # affine_seg_template = pe.Node(interface=GenerateTemplate(),
    #                               name='affine_seg_template')
    # wf.connect(affine_seg_4d_template, 'merged_file', affine_seg_template, 'input_file')
    #
    # nonlinear_registration = pe.MapNode(interface=fsl.FNIRT(),
    #                                     iterfield=['in_file', 'affine_file'],
    #                                     name='nonlinear_registration')
    # nonlinear_registration.inputs.fieldcoeff_file = True
    # wf.connect(input_node, 'seg_files', nonlinear_registration, 'in_file')
    # wf.connect(affine_registration, 'out_matrix_file', nonlinear_registration, 'affine_file')
    # wf.connect(affine_template, 'template_file', nonlinear_registration, 'ref_file')
    #
    # nonlinear_4d_template = pe.Node(interface=fsl.Merge(),
    #                              name='nonlinear_4d_template')
    # nonlinear_4d_template.inputs.dimension = 't'
    # wf.connect(nonlinear_registration, 'warped_file', nonlinear_4d_template, 'in_files')
    #
    # nonlinear_template = pe.Node(interface=GenerateTemplate(),
    #                           name='nonlinear_template')
    # wf.connect(nonlinear_4d_template, 'merged_file', nonlinear_template, 'input_file')
    #
    # nonlinear_seg_transform = pe.MapNode(interface=fsl.ApplyWarp(), iterfield=['in_file', 'field_file'], name='nonlinear_seg_transform')
    # wf.connect(input_node, 'seg_files', nonlinear_seg_transform, 'in_file')
    # wf.connect(nonlinear_registration, 'field_file', nonlinear_seg_transform, 'field_file')
    # wf.connect(affine_template, 'template_file', nonlinear_seg_transform, 'ref_file')
    #
    # nonlinear_seg_4d_template = pe.Node(interface=fsl.Merge(),
    #                                 name='nonlinear_seg_4d_template')
    # nonlinear_seg_4d_template.inputs.dimension = 't'
    # wf.connect(nonlinear_seg_transform, 'out_file', nonlinear_seg_4d_template, 'in_files')
    #
    # nonlinear_seg_template = pe.Node(interface=GenerateTemplate(),
    #                              name='nonlinear_seg_template')
    # wf.connect(nonlinear_seg_4d_template, 'merged_file', nonlinear_seg_template, 'input_file')
    #
    # # Split here into a separate workflow
    # final_registration = pe.MapNode(interface=fsl.FNIRT(), iterfield=['in_file', 'affine_file'],
    #                                     name='final_registration')
    # final_registration.inputs.fieldcoeff_file = True
    # final_registration.inputs.jacobian_file = True
    # wf.connect(input_node, 'seg_files', final_registration, 'in_file')
    # wf.connect(affine_registration, 'out_matrix_file', final_registration, 'affine_file')
    # wf.connect(nonlinear_template, 'template_file', final_registration, 'ref_file')
    #
    # final_seg_transform = pe.MapNode(interface=fsl.ApplyWarp(), iterfield=['in_file', 'field_file'],
    #                                      name='final_seg_transform')
    # wf.connect(input_node, 'seg_files', final_seg_transform, 'in_file')
    # wf.connect(final_registration, 'field_file', final_seg_transform, 'field_file')
    # wf.connect(nonlinear_template, 'template_file', final_seg_transform, 'ref_file')
    #
    # spine_mul_jac = pe.MapNode(interface=fsl.ImageMaths(), iterfield=['in_file', 'in_file2'], name='spine_mul_jac')
    # spine_mul_jac.inputs.op_string = '-mul'
    # wf.connect(final_registration, 'jacobian_file', spine_mul_jac, 'in_file')
    # wf.connect(final_seg_transform, 'out_file', spine_mul_jac, 'in_file2')
    #
    # spine_merge = pe.Node(interface=fsl.Merge(),
    #                    name='spine_merge')
    # spine_merge.inputs.dimension = 't'
    # wf.connect(final_seg_transform, 'out_file', spine_merge, 'in_files')
    #
    # spine_mod_merge = pe.Node(interface=fsl.Merge(),
    #                        name='spine_mod_merge')
    # spine_mod_merge.inputs.dimension = 't'
    # wf.connect(spine_mul_jac, 'out_file', spine_mod_merge, 'in_files')
    #
    # spine_mask = pe.Node(interface=fsl.ImageMaths(), name='spine_mask')
    # spine_mask.inputs.op_string = '-Tmean -thr 0.01 -bin'
    # spine_mask.inputs.out_data_type = 'char'
    # wf.connect(spine_merge, 'merged_file', spine_mask, 'in_file')
    #
    # gaussian_filter = pe.Node(interface=fsl.ImageMaths(), name='gaussian')
    # gaussian_filter.inputs.op_string = '-s 1'
    # wf.connect(spine_mod_merge, 'merged_file', gaussian_filter, 'in_file')
    #
    # init_randomise = pe.Node(interface=fsl.model.Randomise(), name='randomise')
    # init_randomise.inputs.base_name = 'GM_mod_merg_s1'
    # wf.connect(gaussian_filter, 'out_file', init_randomise, 'in_file')
    # wf.connect(spine_mask, 'out_file', init_randomise, 'mask')
    # wf.connect(input_node, 'design_mat', init_randomise, 'design_mat')
    # wf.connect(input_node, 'tcon', init_randomise, 'tcon')

    return wf

# def create_spine_vbm_workflow(output_root):
#    wf = pe.Workflow(name='spine_vbm', base_dir=os.path.join(output_root, 'spine_vbm'))

    #input_node = pe.Node(
    #    interface=util.IdentityInterface(fields=['spine_files', 'seg_files', 'template', 'design_mat', 'tcon']),
    #    name='input_node')



    #Nonlinear registration to template

    #Update

    #Final registration to template


