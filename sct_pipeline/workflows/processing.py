import os  # system functions

#from nipype import Workflow, Node, IdentityInterface

import nipype.interfaces.fsl as fsl
import nipype.interfaces.ants as ants
import nipype.pipeline.engine as pe
import nipype.interfaces.utility as util

#from sct_pipeline.interfaces.segmentation import SCTDeepSeg, SCTLabelVertebrae, SCTRegisterToTemplate
import sct_pipeline.interfaces.registration as sct_reg
import sct_pipeline.interfaces.segmentation as sct_seg
import sct_pipeline.interfaces.util as sct_util
import sct_pipeline.interfaces.dmri as sct_dmri

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

    input_node = pe.Node(pe.IdentityInterface(['t2_image']), 'input_node')

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

    input_node = pe.Node(pe.IdentityInterface(['dwi_image', 'bvals', 'bvecs']), 'input_node')

    #First part of this pipeline is to generate an approximate DWI mask for motion correction
    mean_dwi = pe.Node(sct_util.Mean(), 'mean_dwi')
    mean_dwi.inputs.dimension = 't'
    wf.connect(input_node, 'dwi_image', mean_dwi, 'input_image')

    #Rough segmentation of dwi (DeepSeg is used later as the final segmentation)
    initial_spine_segmentation = pe.Node(sct_seg.PropSeg(), 'initial_spine_segmentation')
    initial_spine_segmentation.inputs.contrast = 'dwi'
    wf.connect(mean_dwi, 'mean_image', initial_spine_segmentation, 'input_image')

    #Create a mask that is 35mm from the spine centerline
    create_mask = pe.Node(sct_seg.CreateMask(), 'create_mask')
    create_mask.inputs.size = 35
    wf.connect(mean_dwi, 'mean_image', create_mask, 'input_image')
    wf.connect(initial_spine_segmentation, 'centerline_file', create_mask, 'centerline_image')

    dmri_moco = pe.Node(sct_dmri.MotionCorrection(), name='dmri_moco')
    wf.connect(input_node, 'dwi_image', dmri_moco, 'dwi_image')
    wf.connect(input_node, 'bvals', dmri_moco, 'bvec')
    wf.connect(input_node, 'bvecs', dmri_moco, 'bval')
    wf.connect(create_mask, 'mask_file', dmri_moco, 'mask')

    #Re-segment the spine, then finish the DWI processing
    spine_segmentation = pe.Node(sct_seg.DeepSeg(), name='spine_segmentation')
    spine_segmentation.inputs.contrast = 'dwi'
    wf.connect(dmri_moco, 'moco_dwi', spine_segmentation, 'input_image')

    sct_dmri_compute_dti