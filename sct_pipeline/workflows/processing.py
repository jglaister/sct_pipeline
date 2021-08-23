import os  # system functions

from nipype import Workflow, Node, IdentityInterface

from sct_pipeline.interfaces.segmentation import SCTDeepSeg, SCTLabelVertebrae, SCTRegisterToTemplate


class PipelineWorkflow(Workflow):
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

    wf = Workflow(name, scan_directory)

    input_node = Node(IdentityInterface(["t2_image"]), "inputnode")

    sct_deepseg = Node(SCTDeepSeg(), 'sct_deepseg')
    sct_deepseg.inputs.contrast = 't2'
    sct_deepseg.inputs.threshold = 1.0
    wf.connect([(input_node, sct_deepseg, [('t2_image', 'input_image')])])

    sct_label_vertebrae = Node(SCTLabelVertebrae(), 'sct_label_vertebrae')
    sct_label_vertebrae.inputs.contrast = 't2'
    wf.connect([(sct_deepseg, sct_label_vertebrae, [('spine_segmentation', 'input_image')])])

    sct_register_to_template = Node(SCTRegisterToTemplate(), 'sct_register_to_template')

    #sct_warp_template
    #sct_process_segmentation


