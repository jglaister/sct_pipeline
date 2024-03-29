import os  # system functions

import nipype.pipeline.engine as pe
import nipype.interfaces.utility as util
import nipype.interfaces.ants as ants
import nipype.interfaces.base as base
import nipype.interfaces.fsl as fsl

import sct_pipeline.interfaces.registration as sct_reg
import sct_pipeline.interfaces.segmentation as sct_seg
import sct_pipeline.interfaces.util as sct_util


def spine_label_registration(name, deformable=False):
    registration_node = pe.MapNode(interface=ants.Registration(),
                                         iterfield=['moving_image'],
                                         name=name)
    registration_node.inputs.dimension = 3
    registration_node.inputs.interpolation = 'Linear'
    registration_node.inputs.metric = [['MI', 'MeanSquares', 'MeanSquares'],
                                             ['MI', 'MeanSquares', 'MeanSquares'],
                                             ['MI', 'MeanSquares', 'MeanSquares']]
    if deformable:
        registration_node.inputs.metric_weight = [[0.4, 0.3, 0.3], [0.4, 0.3, 0.3], [0.4, 0.3, 0.3]]
        registration_node.inputs.radius_or_number_of_bins = [[32, 5, 5], [32, 5, 5], [32, 5, 5]]
        registration_node.inputs.sampling_strategy = [['Regular', 'Regular', 'Regular'],
                                                            ['Regular', 'Regular', 'Regular'],
                                                            ['Regular', 'Regular', 'Regular']]
        registration_node.inputs.sampling_percentage = [[0.25, 0.25, 0.25], [0.25, 0.25, 0.25], [0.25, 0.25, 0.25]]
        registration_node.inputs.transforms = ['Rigid', 'Affine', 'SyN']
        registration_node.inputs.transform_parameters = [(0.1,), (0.1,), (0.1, 3, 0)]
        registration_node.inputs.number_of_iterations = [[100, 50, 25], [100, 50, 25], [100, 10, 5]]
        registration_node.inputs.convergence_threshold = [1e-6, 1e-6, 1e-4]
        registration_node.inputs.convergence_window_size = [10, 10, 10]
        registration_node.inputs.smoothing_sigmas = [[4, 2, 1], [4, 2, 1], [2, 1, 0]]
        registration_node.inputs.sigma_units = ['vox', 'vox', 'vox']
        registration_node.inputs.shrink_factors = [[4, 2, 1], [4, 2, 1], [4, 2, 1]]
    else: #affine
        registration_node.inputs.metric_weight = [[0.4, 0.3, 0.3], [0.4, 0.3, 0.3]]
        registration_node.inputs.radius_or_number_of_bins = [[32, 5, 5], [32, 5, 5]]
        registration_node.inputs.sampling_strategy = [['Regular', 'Regular', 'Regular'],
                                                      ['Regular', 'Regular', 'Regular']]
        registration_node.inputs.sampling_percentage = [[0.25, 0.25, 0.25], [0.25, 0.25, 0.25]]
        registration_node.inputs.transforms = ['Rigid', 'Affine']
        registration_node.inputs.transform_parameters = [(0.1,), (0.1,)]
        registration_node.inputs.number_of_iterations = [[100, 50, 25], [100, 50, 25]]
        registration_node.inputs.convergence_threshold = [1e-6, 1e-6]
        registration_node.inputs.convergence_window_size = [10, 10]
        registration_node.inputs.smoothing_sigmas = [[4, 2, 1], [4, 2, 1]]
        registration_node.inputs.sigma_units = ['vox', 'vox']
        registration_node.inputs.shrink_factors = [[4, 2, 1], [4, 2, 1]]

    registration_node.inputs.write_composite_transform = True
    registration_node.inputs.initial_moving_transform_com = 1
    registration_node.inputs.output_warped_image = True

    return registration_node

def create_spine_template_workflow(output_root, init_template_index=0, max_label=9):
    # TODO: Split into seperate workflows
    # Segmentation, template registration/formation, vbm analysis
    wf = pe.Workflow(name='spine_template', base_dir=output_root)

    input_node = pe.Node(interface=util.IdentityInterface(fields=['spine_files', 'design_mat', 'tcon']),
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

    # TODO: Split here into a separate workflow
    threshold_labels = pe.Node(sct_util.ThresholdLabels(), name='threshold_labels')
    threshold_labels.inputs.threshold = True
    threshold_labels.inputs.num_additional_labels_removed = 1
    wf.connect(straighten_labels, 'output_file', threshold_labels, 'label_files')

    # Select the template_index element of the straightened spinalcord to use as the initial template
    select_init_template = pe.Node(interface=util.Select(),
                                   name='select_init_template')
    select_init_template.inputs.index = [init_template_index]
    wf.connect(straighten_spinalcord, 'straightened_input', select_init_template, 'inlist')

    select_init_label = pe.Node(interface=util.Select(),
                                name='select_init_label')
    select_init_label.inputs.index = [init_template_index]
    wf.connect(threshold_labels, 'thresholded_label_files', select_init_label, 'inlist')

    select_init_seg = pe.Node(interface=util.Select(),
                              name='select_init_seg')
    select_init_seg.inputs.index = [init_template_index]
    wf.connect(straighten_segmentation, 'output_file', select_init_seg, 'inlist')

    merge_moving_images = pe.MapNode(interface=util.Merge(3), 
                                     iterfield=['in1', 'in2', 'in3'],
                                     name='merge_moving_images')
    wf.connect(straighten_spinalcord, 'straightened_input', merge_moving_images, 'in1')
    wf.connect(straighten_segmentation, 'output_file', merge_moving_images, 'in2')
    wf.connect(threshold_labels, 'thresholded_label_files', merge_moving_images, 'in3')
    
    merge_fixed_images = pe.Node(interface=util.Merge(3), 
                                 name='merge_fixed_images')
    wf.connect(select_init_template, 'out', merge_fixed_images, 'in1')
    wf.connect(select_init_seg, 'out', merge_fixed_images, 'in2')
    wf.connect(select_init_label, 'out', merge_fixed_images, 'in3')
    
    affine_registration = pe.MapNode(interface=ants.Registration(),
                                     iterfield=['moving_image'],
                                     name='affine_registration')
    affine_registration.inputs.dimension = 3
    affine_registration.inputs.interpolation = 'Linear'
    affine_registration.inputs.metric = [['MI', 'MeanSquares', 'MeanSquares'], ['MI', 'MeanSquares', 'MeanSquares']]
    affine_registration.inputs.metric_weight = [[0.4, 0.3, 0.3], [0.4, 0.3, 0.3]]
    affine_registration.inputs.radius_or_number_of_bins = [[32, 5, 5], [32, 5, 5]]
    affine_registration.inputs.sampling_strategy = [['Regular', 'Regular', 'Regular'], ['Regular', 'Regular', 'Regular']]
    affine_registration.inputs.sampling_percentage = [[0.25, 0.25, 0.25], [0.25, 0.25, 0.25]]
    affine_registration.inputs.transforms = ['Rigid', 'Affine']
    affine_registration.inputs.transform_parameters = [(0.1,), (0.1,)]
    affine_registration.inputs.number_of_iterations = [[100, 50, 25], [100, 50, 25]]
    affine_registration.inputs.convergence_threshold = [1e-6, 1e-6]
    affine_registration.inputs.convergence_window_size = [10, 10]
    affine_registration.inputs.smoothing_sigmas = [[4, 2, 1], [4, 2, 1]]
    affine_registration.inputs.sigma_units = ['vox', 'vox']
    affine_registration.inputs.shrink_factors = [[4, 2, 1], [4, 2, 1]]
    affine_registration.inputs.write_composite_transform = True
    affine_registration.inputs.initial_moving_transform_com = 1
    affine_registration.inputs.output_warped_image = True
    wf.connect(merge_moving_images, 'out', affine_registration, 'moving_image')
    wf.connect(merge_fixed_images, 'out', affine_registration, 'fixed_image')

    affine_4d_template = pe.Node(interface=fsl.Merge(),
                                name='affine_4d_template')
    affine_4d_template.inputs.dimension = 't'
    wf.connect(affine_registration, 'warped_image', affine_4d_template, 'in_files')

    affine_template = pe.Node(interface=sct_util.GenerateTemplate(),
                              name='affine_template')
    wf.connect(affine_4d_template, 'merged_file', affine_template, 'input_file')

    affine_warp_labels = pe.MapNode(interface=ants.ApplyTransforms(),
                                    iterfield=['input_image', 'reference_image', 'transforms'])
    affine_warp_labels.inputs.interpolation = 'NearestNeighbor'
    wf.connect(threshold_labels, 'thresholded_label_files', affine_warp_labels, 'input_image')
    wf.connect(affine_registration, 'warped_image', affine_warp_labels, 'reference_image')
    wf.connect(affine_registration, 'forward_transforms', affine_warp_labels, 'transforms')

    #Handle l-r flip
    affine_labels = pe.Node(interface=sct_seg.LabelFusion(),
                            name='affine_labels')
    affine_labels.inputs.operation = 'MajorityVoting'
    wf.connect(affine_warp_labels, 'output_image', affine_labels, 'images')

    affine_warp_seg = pe.MapNode(interface=ants.ApplyTransforms(),
                                 iterfield=['input_image', 'reference_image', 'transforms'],
                                 name='affine_warp_seg')
    affine_warp_seg.inputs.interpolation = 'Linear'
    wf.connect(straighten_segmentation, 'output_file', affine_warp_seg, 'input_image')
    wf.connect(affine_registration, 'warped_image', affine_warp_seg, 'reference_image')
    wf.connect(affine_registration, 'forward_transforms', affine_warp_seg, 'transforms')

    affine_4d_seg = pe.Node(interface=fsl.Merge(),
                            name='affine_4d_seg')
    affine_4d_seg.inputs.dimension = 't'
    wf.connect(affine_warp_seg, 'output_image', affine_4d_seg, 'in_files')

    affine_seg = pe.Node(interface=sct_util.GenerateTemplate(),
                         name='affine_seg')
    wf.connect(affine_4d_template, 'merged_file', affine_seg, 'input_file')

    merge_fixed_images_affine = pe.Node(interface=util.Merge(3),
                                 name='merge_fixed_images_affine')
    wf.connect(affine_template, 'template_file', merge_fixed_images_affine, 'in1')
    wf.connect(affine_seg, 'template_file', merge_fixed_images_affine, 'in2')
    wf.connect(affine_labels, 'output_image', merge_fixed_images_affine, 'in3')

    deformable_registration = pe.MapNode(interface=ants.Registration(),
                                     iterfield=['moving_image'],
                                     name='deformable_registration')
    deformable_registration.inputs.dimension = 3
    deformable_registration.inputs.interpolation = 'Linear'
    deformable_registration.inputs.metric = [['MI', 'MeanSquares', 'MeanSquares'],
                                             ['MI', 'MeanSquares', 'MeanSquares'],
                                             ['MI', 'MeanSquares', 'MeanSquares']]
    deformable_registration.inputs.metric_weight = [[0.4, 0.3, 0.3], [0.4, 0.3, 0.3], [0.4, 0.3, 0.3]]
    deformable_registration.inputs.radius_or_number_of_bins = [[32, 5, 5], [32, 5, 5], [32, 5, 5]]
    deformable_registration.inputs.sampling_strategy = [['Regular', 'Regular', 'Regular'],
                                                        ['Regular', 'Regular', 'Regular'],
                                                        ['Regular', 'Regular', 'Regular']]
    deformable_registration.inputs.sampling_percentage = [[0.25, 0.25, 0.25], [0.25, 0.25, 0.25], [0.25, 0.25, 0.25]]
    deformable_registration.inputs.transforms = ['Rigid', 'Affine', 'SyN']
    deformable_registration.inputs.transform_parameters = [(0.1,), (0.1,), (0.1, 3, 0)]
    deformable_registration.inputs.number_of_iterations = [[100, 50, 25], [100, 50, 25], [100, 10, 5]]
    deformable_registration.inputs.convergence_threshold = [1e-6, 1e-6, 1e-4]
    deformable_registration.inputs.convergence_window_size = [10, 10, 10]
    deformable_registration.inputs.smoothing_sigmas = [[4, 2, 1], [4, 2, 1], [2, 1, 0]]
    deformable_registration.inputs.sigma_units = ['vox', 'vox', 'vox']
    deformable_registration.inputs.shrink_factors = [[4, 2, 1], [4, 2, 1], [4, 2, 1]]
    deformable_registration.inputs.write_composite_transform = True
    deformable_registration.inputs.initial_moving_transform_com = 1
    deformable_registration.inputs.output_warped_image = True
    wf.connect(merge_moving_images, 'out', deformable_registration, 'moving_image')
    wf.connect(merge_fixed_images_affine, 'out', deformable_registration, 'fixed_image')

    #TODO: Compartmentalize reusable deformation segments

    deformable_4d_template = pe.Node(interface=fsl.Merge(),
                                 name='deformable_4d_template')
    deformable_4d_template.inputs.dimension = 't'
    wf.connect(deformable_registration, 'warped_image', deformable_4d_template, 'in_files')

    deformable_template = pe.Node(interface=sct_util.GenerateTemplate(),
                              name='deformable_template')
    wf.connect(deformable_4d_template, 'merged_file', deformable_template, 'input_file')

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



