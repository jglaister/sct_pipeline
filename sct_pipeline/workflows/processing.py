import os  # system functions

#from nipype import Workflow, Node, IdentityInterface

import nipype.interfaces.io as io
import nipype.interfaces.fsl as fsl
import nipype.interfaces.ants as ants
import nipype.pipeline.engine as pe
import nipype.interfaces.utility as util

import sct_pipeline.interfaces.registration as sct_reg
import sct_pipeline.interfaces.segmentation as sct_seg
import sct_pipeline.interfaces.util as sct_util
import sct_pipeline.interfaces.dmri as sct_dmri

# from fpdf import FPDF
# from PIL.Image import Image

class PipelineWorkflow(pe.Workflow):
    def __init__(self, name, scan_directory, patient_id=None, scan_id=None):
        self.scan_directory = scan_directory
        self.patient_id = patient_id if patient_id is not None else ''
        if scan_id is None or scan_id == '':
            self.scan_id = ''
        else:
            self.scan_id = scan_id
            name += '_' + scan_id
        base_dir = os.path.join(scan_directory, self.patient_id, 'pipeline')
        super(PipelineWorkflow, self).__init__(name, base_dir)
        # self.config['execution']['crashdump_dir'] = os.path.join(self.base_dir, self.name)

    # def clean(self):
    #    shutil.rmtree(os.path.join(self.base_dir, self.name))
    #    if os.path.basename(self.base_dir) == 'pipeline' and os.listdir(self.base_dir) == []:
    #        shutil.rmtree(self.base_dir)

'''def create_spinalcord_mtr_workflow(scan_directory, patient_id=None, scan_id=None, compute_csa=False):

    name = 'SCT_MTR'
    if patient_id is not None and scan_id is not None:
        scan_directory = os.path.join(scan_directory, patient_id, 'pipeline')
        name += '_' + scan_id

    wf = Workflow(name, scan_directory)

    input_node = Node(IdentityInterface(["mt_on_sc_image", "mt_off_sc_image"]), "inputnode")

    sct_deepseg = Node(SCTDeepSeg(),'sct_deepseg')
    sct_deepseg.inputs.contrast = 't2'
    wf.connect([(input_node, sct_deepseg, [('mt_on_sc_image', 'input_image')])])

    sct_createmask = Node(SCTCreateMask(),'sct_createmask')
    sct_createmask.inputs.size = 35
    sct_createmask.inputs.process = 'centerline'
    sct_createmask.inputs.shape = 'cylinder'
    wf.connect([(input_node, sct_createmask, [('mt_on_sc_image', 'input_image')])])
    wf.connect([(sct_deepseg, sct_createmask, [('centerline', 'process_image')])])

    sct_registermultimodal = Node(SCTRegisterMultimodal(),'sct_registermultimodal')
    wf.connect([(input_node, sct_registermultimodal, [('mt_on_sc_image', 'dest_image')])])
    wf.connect([(input_node, sct_registermultimodal, [('mt_off_sc_image', 'input_image')])])
'''


def create_spinalcord_t2_workflow(scan_directory, patient_id=None, scan_id=None):
    name = 'SCT_T2'
    if patient_id is not None and scan_id is not None:
        scan_directory = os.path.join(scan_directory, patient_id, 'pipeline')
        name += '_' + scan_id

    wf = pe.Workflow(name, scan_directory)

    input_node = pe.Node(util.IdentityInterface(['t2_image']), 'input_node')

    spine_segmentation = pe.Node(sct_seg.DeepSeg(), 'spine_segmentation')
    spine_segmentation.inputs.contrast = 't2'
    spine_segmentation.inputs.threshold = 1.0
    wf.connect([(input_node, spine_segmentation, [('t2_image', 'input_image')])])

    sct_label_vertebrae = pe.Node(sct_seg.LabelVertebrae(), 'label_vertebrae')
    sct_label_vertebrae.inputs.contrast = 't2'
    wf.connect([(spine_segmentation, sct_label_vertebrae, [('spine_segmentation', 'input_image')])])

    sct_register_to_template = pe.Node(sct_reg.RegisterToTemplate(), 'register_to_template')

    #sct_warp_template
    #sct_process_segmentation

def create_spinalcord_dti_workflow(scan_directory, patient_id=None, scan_id=None):
    name = 'SCT_DTI'
    if patient_id is not None and scan_id is not None:
        scan_directory = os.path.join(scan_directory, patient_id, 'pipeline')
        name += '_' + scan_id

    wf = pe.Workflow(name, scan_directory)

    input_node = pe.Node(util.IdentityInterface(['dwi_file', 'bval_file', 'bvec_file']), 'input_node')

    # First part of this pipeline is to generate an approximate DWI mask for motion correction
    mean_dwi = pe.Node(sct_util.Mean(), 'mean_dwi')
    mean_dwi.inputs.dimension = 't'
    wf.connect(input_node, 'dwi_image', mean_dwi, 'input_image')

    # Rough segmentation of dwi (DeepSeg is used later as the final segmentation)
    initial_spine_segmentation = pe.Node(sct_seg.PropSeg(), 'initial_spine_segmentation')
    initial_spine_segmentation.inputs.contrast = 'dwi'
    wf.connect(mean_dwi, 'mean_image', initial_spine_segmentation, 'input_image')

    # Create a mask that is 35mm from the spine centerline
    create_mask = pe.Node(sct_seg.CreateMask(), 'create_mask')
    create_mask.inputs.size = 35
    wf.connect(mean_dwi, 'mean_image', create_mask, 'input_image')
    wf.connect(initial_spine_segmentation, 'centerline_file', create_mask, 'centerline_image')

    motion_correction = pe.Node(sct_dmri.MotionCorrection(), name='motion_correction')
    wf.connect(input_node, 'dwi_image', motion_correction, 'dwi_image')
    wf.connect(input_node, 'bvals', motion_correction, 'bvec')
    wf.connect(input_node, 'bvecs', motion_correction, 'bval')
    wf.connect(create_mask, 'mask_file', motion_correction, 'mask')

    # Re-segment the spine, then finish the DWI processing
    spine_segmentation = pe.Node(sct_seg.DeepSeg(), name='spine_segmentation')
    spine_segmentation.inputs.contrast = 'dwi'
    wf.connect(motion_correction, 'moco_dwi', spine_segmentation, 'input_image')

    # sct_dmri_compute_dti


def create_spinalcord_mtr_workflow(scan_directory, patient_id=None, scan_id=None,
                                   compute_csa=False, compute_avggmwm=False, use_iacl_struct=False):
    name = 'SCT_MTR'
    vert = '3:4'  # This is consistent with what I provided Tony Kang for his RIS spinal cord study
    # TODO: Add corrected MTR
    root_dir = scan_directory
    if use_iacl_struct is True:
        if patient_id is not None and scan_id is not None:
            root_dir = os.path.join(root_dir, patient_id, 'pipeline')
            name += '_' + scan_id
        else:
            raise ValueError('Need to provide a patient_id and scan_id to use the IACL folder structure')
    else:
        if patient_id is not None:
            scan_folder = patient_id + '_' + scan_id if scan_id is not None else patient_id
            root_dir = (os.path.join(root_dir, scan_folder))
        # else just use the scan_directory

    wf = pe.Workflow(name, root_dir)

    input_node = pe.Node(util.IdentityInterface(['mton_file', 'mtoff_file']), 'input_node')

    #TODO: Investigate if smoothing is needed
    spine_segmentation = pe.Node(sct_seg.DeepSeg(), name='spine_segmentation')
    spine_segmentation.inputs.contrast = 't2'
    wf.connect(input_node, 'mton_file', spine_segmentation, 'input_image')

    create_mask = pe.Node(sct_seg.CreateMask(), 'create_mask')
    create_mask.inputs.size_in_mm = 41  # Default not in mm. Does this affect things?
    wf.connect(input_node, 'mton_file', create_mask, 'input_image')
    wf.connect(spine_segmentation, 'spine_segmentation', create_mask, 'centerline_image')

    register_multimodal = pe.Node(sct_reg.RegisterMultimodal(), 'register_mtoff_to_mton')
    register_multimodal.inputs.param = 'step=1,type=im,algo=slicereg,metric=CC'
    register_multimodal.inputs.interpolation = 'spline'
    wf.connect(input_node, 'mtoff_file', register_multimodal, 'input_image')
    wf.connect(input_node, 'mton_file', register_multimodal, 'destination_image')
    wf.connect(create_mask, 'mask_file', register_multimodal, 'mask')

    compute_mtr = pe.Node(sct_util.ComputeMTR(), 'compute_mtr')
    wf.connect(register_multimodal, 'warped_input_image', compute_mtr, 'mt_off_image')
    wf.connect(input_node, 'mton_file', compute_mtr, 'mt_on_image')

    # Assumes the FOV is centered at the c3c4 disc
    label_utils = pe.Node(sct_util.LabelUtils(), 'label_utils')
    label_utils.inputs.output_file = 'c3c4.nii.gz'
    label_utils.inputs.create_seg_mid = 4
    wf.connect(spine_segmentation, 'spine_segmentation', label_utils, 'input_image')

    template_registration = pe.Node(sct_reg.RegisterToTemplate(), 'template_registration')
    template_registration.inputs.reference = 'subject'
    template_registration.inputs.param = 'step=1,type=seg,algo=centermassrot:step=2,type=seg,algo=bsplinesyn,slicewise=1'
    # Parameters come from the SCT MT example
    wf.connect(input_node, 'mton_file', template_registration, 'input_image')
    wf.connect(spine_segmentation, 'spine_segmentation', template_registration, 'spine_segmentation')
    wf.connect(label_utils, 'label_image', template_registration, 'disc_labels')

    warp_template = pe.Node(sct_reg.WarpTemplate(), 'warp_template')
    warp_template.inputs.warp_white_matter = 0
    warp_template.inputs.warp_spinal_levels = 0
    wf.connect(input_node,'mton_file', warp_template,'destination_image')
    wf.connect(template_registration, 'warp_template2anat', warp_template,'warping_field')

    #TODO: C2/C4 points
    #TODO: Template registration?
    extract_mtr = pe.Node(sct_util.ExtractMetric(), 'extract_mtr')
    extract_mtr.inputs.vertebrae = vert
    extract_mtr.inputs.per_slice = 1
    wf.connect(compute_mtr, 'mtr_image', extract_mtr, 'input_image')
    wf.connect(warp_template, 'levels', extract_mtr, 'vertebrae_image')
    wf.connect(warp_template, 'cord', extract_mtr, 'label_image')

    if compute_csa:
        process_seg = pe.Node(sct_util.ProcessSeg(), 'process_seg')
        process_seg.inputs.vertebrae = vert
        process_seg.inputs.per_slice = 1
        wf.connect(warp_template, 'cord', process_seg, 'input_image')
        wf.connect(warp_template, 'levels', process_seg, 'vertebrae_image')

    if compute_avggmwm:
        compute_avg_gmwm_mtr = pe.Node(sct_util.ComputeAvgGMWMMTR(), 'compute_avg_gmwm_mtr')
        wf.connect(compute_mtr, 'mtr_image', compute_avg_gmwm_mtr, 'mtr_file')
        wf.connect(warp_template, 'gm', compute_avg_gmwm_mtr, 'gm_file')
        wf.connect(warp_template, 'wm', compute_avg_gmwm_mtr, 'wm_file')

    # Set up base filename for copying outputs
    if use_iacl_struct:
        out_file_base = os.path.join(scan_directory, patient_id, scan_id, patient_id + '_' + scan_id + '_SPINE')
    else:
        if patient_id is not None:
            out_file_base = patient_id + '_' + scan_id if scan_id is not None else patient_id
        else:
            out_file_base = 'out'
        out_file_base = os.path.join(scan_directory, out_file_base + '_SPINE')

    # Use the template warped cord segmentation as the final spine segmentation
    # I've found this to be a smoother result IF the registration is successful
    # Whereas the DeepSeg result is boxier, but may be better if the template
    # can't register to the spine (this happens more with T2 spines)
    export_segmentation = pe.Node(io.ExportFile(), name='export_segmentation')
    export_segmentation.inputs.check_extension = True
    export_segmentation.inputs.clobber = True
    export_segmentation.inputs.out_file = out_file_base + '_seg.nii.gz'
    wf.connect(warp_template, 'cord', export_segmentation, 'in_file')

    export_mtr = pe.Node(io.ExportFile(), name='export_mtr')
    export_mtr.inputs.check_extension = True
    export_mtr.inputs.clobber = True
    export_mtr.inputs.out_file = out_file_base + '_MTR.nii.gz'
    wf.connect(compute_mtr, 'mtr_image', export_mtr, 'in_file')

    export_mton = pe.Node(io.ExportFile(), name='export_mton')
    export_mton.inputs.check_extension = True
    export_mton.inputs.clobber = True
    export_mton.inputs.out_file = out_file_base + '_MT_ON.nii.gz'
    wf.connect(input_node, 'mton_file', export_mton, 'in_file')

    export_mtoff = pe.Node(io.ExportFile(), name='export_mtoff')
    export_mtoff.inputs.check_extension = True
    export_mtoff.inputs.clobber = True
    export_mtoff.inputs.out_file = out_file_base + '_MT_OFF_reg.nii.gz'
    wf.connect(register_multimodal, 'warped_input_image', export_mtoff, 'in_file')

    export_mtr_metric = pe.Node(io.ExportFile(), name='export_mtr_metric')
    export_mtr_metric.inputs.check_extension = True
    export_mtr_metric.inputs.clobber = True
    export_mtr_metric.inputs.out_file = out_file_base + '_MTR_perslice.csv'
    wf.connect(extract_mtr, 'output_csv', export_mtr_metric, 'in_file')

    if compute_csa:
        export_csa_metric = pe.Node(io.ExportFile(), name='export_csa_metric')
        export_csa_metric.inputs.check_extension = True
        export_csa_metric.inputs.clobber = True
        export_csa_metric.inputs.out_file = out_file_base + '_CSA_perslice.csv'
        wf.connect(process_seg, 'output_csv', export_csa_metric, 'in_file')

    if compute_avggmwm:
        export_avggmwm = pe.Node(io.ExportFile(), name='export_avggmwm')
        export_avggmwm.inputs.check_extension = True
        export_avggmwm.inputs.clobber = True
        export_avggmwm.inputs.out_file = out_file_base + '_avg_GM_WM_MTR.csv'
        wf.connect(compute_avg_gmwm_mtr, 'output_csv', export_avggmwm, 'in_file')

    #if True:
        #Write segmentation images to disk

        #Write MTR images to disk


        #Write PDF with images to disk

    return wf


