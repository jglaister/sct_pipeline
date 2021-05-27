import nipype
import os  # system functions
import shutil

import nipype.interfaces.io as nio  # Data i/o
import nipype.interfaces.utility as util  # utility
import nipype.pipeline.engine as pe  # pypeline engine

from nipype import Workflow, Node, MapNode, Function, IdentityInterface
from nipype.interfaces.ants import Registration, AverageImages
from nipype.interfaces.ants import N4BiasFieldCorrection, Registration, ApplyTransforms
from nipype.interfaces.fsl import BET
from nipype.interfaces.fsl import Smooth

from .interfaces import SCTDeepSeg
from nipype.interfaces.ants import MultiplyImages
#from iacl_pipeline.workflows.base import PipelineWorkflow
#TODO: Cropping to spinal cord/remove brain?

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
        self.config['execution']['crashdump_dir'] = os.path.join(self.base_dir, self.name)

    def clean(self):
        shutil.rmtree(os.path.join(self.base_dir, self.name))
        if os.path.basename(self.base_dir) == 'pipeline' and os.listdir(self.base_dir) == []:
            shutil.rmtree(self.base_dir)

def create_spinalcord_mtr_workflow(scan_directory, patient_id=None, scan_id=None, compute_csa=False):

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



