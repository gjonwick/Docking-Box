from pymol.Qt import QtCore
from src.ADContext import ADContext
import logging
from src.utils.util import while_in_dir
from src.api.BaseController import BaseController
from typing import Any


def get_pdbqt(ligand):
    return ligand.pdbqt

class DockingJobController(BaseController):

    def __init__(self, form, callbacks=None):
        super(DockingJobController, self).__init__(form, callbacks)

    def _get_logger(self) -> Any:
        return self.loggerFactory \
            .giff_me_logger(name=__name__,
                            level=logging.DEBUG,
                            destination=self.form.dockingLogBox)

    def run(self):
        form = self.form
        form.runDocking_btn.setEnabled(False)

        form.thread = QtCore.QThread()
        form.worker = VinaWorker(form)
        form.worker.moveToThread(form.thread)
        form.thread.started.connect(form.worker.run)
        form.worker.finished.connect(form.thread.quit)
        form.worker.finished.connect(form.worker.deleteLater)
        # form.thread.finished.connect(form.thread.deleteLater)
        form.worker.finished.connect(self.onFinished)
        form.worker.progress.connect(lambda x: self.logger.info(x))

        # start thread
        form.thread.start()

        # form.thread.finished.connect(
        #     lambda: self.logger.info('Finish!')
        # )

    def onFinished(self, msg):
        self.form.runDocking_btn.setEnabled(True)
        self.logger.info(msg)
        # self.logger.info("I'm DONE!")


class VinaWorker(QtCore.QObject):
    finished = QtCore.pyqtSignal(str)
    progress = QtCore.pyqtSignal(str)

    def __init__(self, form):
        super(VinaWorker, self).__init__()
        self.form = form

    def run(self):
        adContext = ADContext()

        # get working dir
        working_dir = adContext.config['working_dir']

        # make sure tools are loaded
        if not adContext.vina_tools_loaded:
            tools = adContext.load_vina_tools()
            if tools is None:
                self.finished.emit('Vina tools could not be loaded! Please specify the correct path, or load the '
                                   'respective modules!')
                return

        # make sure there are ligands to dock
        ligands_to_dock = adContext.ligands_to_dock
        if len(ligands_to_dock) < 1:
            self.finished.emit('There are no ligands to dock!')
            return

        receptor = adContext.receptor
        if receptor is None:
            self.finished.emit("No receptor loaded! Please generate and load the receptor first!")
            return

        """ When distinguishing between flexible or rigid, the receptor will make the difference. In the 
        case of multiple docking, each ligand will be run on flexible residues if the receptor has flexible residues. 
        If there are ligands to be run with rigid docking, than make sure there is another receptor with rigid residues. 
        """
        # TODO: an option in the docking tab may be added to run flexible or rigid with the selected ligands on the
        #  prepared ligands list.
        with while_in_dir(working_dir):

            try:
                if len(ligands_to_dock) == 1:
                    # basic docking
                    ligand_to_dock = ligands_to_dock[list(ligands_to_dock.keys())[0]]
                    self.basic_docking(ligand_to_dock, receptor)
                else:
                    # batch docking
                    self.multiple_ligand_docking(ligands_to_dock, receptor)

            except Exception as e:
                self.finished.emit(e)

        # # ligands_to_dock = adContext.ligands_to_dock
        #
        # # ligands_to_dock = ['str'] # NOTE: vina probably supports batch docking with multiple ligands
        # # ligand = adContext.ligands['str']
        # # prefix = '/'.join(receptor.pdbqt_location.split('/')[0:-1])
        # # suffix = receptor.pdbqt_location.split('/')[-1]
        # # name = '_'.join(suffix.split('.')[0].split('_')[0:-1])
        #
        # # for stdout_line in p.stdout.readlines():
        # #     self.progress.emit(stdout_line)
        # #     sys.stdout.flush()
        # # form.plainTextEdit.moveCursor(QtGui.QTextCursor.End)
        # # p.stdout.close()

        self.finished.emit('Done :)')

    def basic_docking(self, ligand, receptor):
        """ Function responsible for running docking with only 1 ligand. """
        adContext = ADContext()  # NOTE: (ADContext not yet thread safe)
        flex_docking = True

        if len(receptor.flexible_residues) == 0:
            flex_docking = False

        if flex_docking:
            rigid_receptor = receptor.rigid_pdbqt
            flex_receptor = receptor.flex_pdbqt
            if flex_receptor is not None and rigid_receptor is not None:
                output_file = "vina_result_{}_flexible.pdbqt".format(receptor.name)
                (rc, stdout, stderr) = adContext.vina(receptor=rigid_receptor,
                                                      flex=flex_receptor,
                                                      ligand=ligand.pdbqt,
                                                      config=adContext.config['box_path'],
                                                      exhaustiveness=int(adContext.config['dockingjob_params'][
                                                                             'exhaustiveness']),
                                                      out=output_file)

            else:
                self.finished.emit('An error occurred while processing rigid and flexible structures!')
                return
        else:
            output_file = "vina_result_{}.pdbqt".format(receptor.name)
            (rc, stdout, stderr) = adContext.vina(receptor=receptor.pdbqt_location,
                                                  ligand=ligand.pdbqt,
                                                  config=adContext.config['box_path'],
                                                  exhaustiveness=int(adContext.config['dockingjob_params'][
                                                                         'exhaustiveness']),
                                                  out=output_file)

        self.progress.emit(stdout.decode('utf-8'))
        self.progress.emit("rc = {}".format(rc))

        return rc, stdout, stderr

    def multiple_ligand_docking(self, ligands_to_dock, receptor):

        """ Function responsible for running docking with multiple ligands. """
        # self.logger.error("Multiple ligand docking not implemented yet!")
        adContext = ADContext()
        flex_docking = True
        ligands_pdbqt = list(map(get_pdbqt, list(ligands_to_dock.values())))

        if len(receptor.flexible_residues) == 0:
            flex_docking = False

        if flex_docking:
            rigid_receptor = receptor.rigid_pdbqt
            flex_receptor = receptor.flex_pdbqt
            if flex_receptor is not None and rigid_receptor is not None:
                output_file = "vina_multidock_result_{}_flexible.pdbqt".format(receptor.name)
                (rc, stdout, stderr) = adContext.vina(receptor=rigid_receptor,
                                                      flex=flex_receptor,
                                                      ligand=ligands_pdbqt,
                                                      config=adContext.config['box_path'],
                                                      exhaustiveness=int(adContext.config['dockingjob_params'][
                                                                             'exhaustiveness']),
                                                      out=output_file)

            else:
                self.finished.emit('An error occurred while processing rigid and flexible structures!')
                return
        else:
            output_file = "vina_result_{}.pdbqt".format(receptor.name)
            (rc, stdout, stderr) = adContext.vina(receptor=receptor.pdbqt_location,
                                                  ligand=ligands_pdbqt,
                                                  config=adContext.config['box_path'],
                                                  exhaustiveness=int(adContext.config['dockingjob_params'][
                                                                         'exhaustiveness']),
                                                  out=output_file)

        return rc, stdout, stderr

# sample_command = f'vina --receptor {rigid_receptor} \ --flex {flex_receptor} --ligand {
# ligand_to_dock.pdbqt} \ --config {box_path} \ --exhaustiveness {exhaustiveness} --out
# TESTING_DOCK_{receptor.name}_vina_out.pdbqt'
