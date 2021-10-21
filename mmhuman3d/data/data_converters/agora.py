import os

import numpy as np
import pickle5 as pickle
from tqdm import tqdm

from mmhuman3d.core.conventions.keypoints_mapping import convert_kps
from .base_converter import BaseModeConverter
from .builder import DATA_CONVERTERS


@DATA_CONVERTERS.register_module()
class AgoraConverter(BaseModeConverter):

    ACCEPTED_MODES = ['validation', 'train']

    def __init__(self, modes=[], fit='smpl'):
        super(AgoraConverter, self).__init__(modes)
        accepted_fits = ['smpl', 'smplx']
        if fit not in accepted_fits:
            raise ValueError('Input fit not in accepted fits. \
                Use either smpl or smplx')
        self.fit = fit

    def convert_by_mode(self, dataset_path, out_path, mode):
        # total dictionary to store all data
        total_dict = {}

        # structs we use
        image_path_, bbox_xywh_, keypoints2d_, keypoints3d_ = [], [], [], []

        if self.fit == 'smplx':
            smplx = {}
            smplx['body_pose'] = []
            smplx['global_orient'] = []
            smplx['betas'] = []
            smplx['transl'] = []
            smplx['left_hand_pose'] = []
            smplx['right_hand_pose'] = []
            smplx['expression'] = []
            smplx['leye_pose'] = []
            smplx['reye_pose'] = []
            smplx['jaw_pose'] = []
        else:
            smpl = {}
            smpl['body_pose'] = []
            smpl['global_orient'] = []
            smpl['betas'] = []
            smpl['transl'] = []

        meta = {}
        meta['gender'] = []
        meta['age'] = []
        meta['ethnicity'] = []
        meta['kid'] = []
        meta['occlusion'] = []

        # get a list of .pkl files in the directory
        img_path = os.path.join(dataset_path, 'images', mode)
        annot_path = os.path.join(dataset_path, 'camera_dataframe')

        # go through all the .pkl files
        annot_dataframes = [
            os.path.join(annot_path, f) for f in os.listdir(annot_path)
            if f.endswith('.pkl') and '{}'.format(mode) in f
        ]

        for filename in tqdm(sorted(annot_dataframes)):
            df = pickle.load(open(filename, 'rb'))
            for idx in range(len(df)):
                imgname = df.iloc[idx]['imgPath']
                img_path = os.path.join('images', imgname)
                valid_pers_idx = np.where(df.iloc[idx].at['isValid'])[0]
                for pidx in valid_pers_idx:
                    # obtain meta data
                    gender = df.iloc[idx]['gender'][pidx]
                    age = df.iloc[idx]['age'][pidx]
                    kid = df.iloc[idx]['kid'][pidx]
                    occlusion = df.iloc[idx]['occlusion'][pidx]
                    ethnicity = df.iloc[idx]['ethnicity'][pidx]

                    # obtain keypoints
                    keypoints2d = df.iloc[idx]['gt_joints_2d'][pidx]
                    keypoints3d = df.iloc[idx]['gt_joints_3d'][pidx]

                    # add confidence column
                    keypoints2d = np.hstack([keypoints2d, np.ones((127, 1))])
                    keypoints3d = np.hstack([keypoints3d, np.ones((127, 1))])

                    bbox_xyxy = [
                        min(keypoints2d[:, 0]),
                        min(keypoints2d[:, 1]),
                        max(keypoints2d[:, 0]),
                        max(keypoints2d[:, 1])
                    ]
                    bbox_xywh = self._bbox_expand(bbox_xyxy, scale_factor=1.2)

                    keypoints2d_.append(keypoints2d)
                    keypoints3d_.append(keypoints3d)
                    bbox_xywh_.append(bbox_xywh)
                    image_path_.append(img_path)

                    meta['gender'].append(gender)
                    meta['age'].append(age)
                    meta['kid'].append(kid)
                    meta['occlusion'].append(occlusion)
                    meta['ethnicity'].append(ethnicity)

                    if self.fit == 'smplx':
                        # obtain smplx data
                        gt_smplx_path = os.path.join(
                            dataset_path, df.iloc[idx]['gt_path_smplx'][pidx])
                        gt_smplx_path = gt_smplx_path.replace('.obj', '.pkl')
                        gt_smplx = pickle.load(open(gt_smplx_path, 'rb'))

                        smplx['body_pose'].append(
                            gt_smplx['body_pose'].reshape((21, 3)))
                        smplx['global_orient'].append(
                            gt_smplx['global_orient'])
                        smplx['betas'].append(gt_smplx['betas'])
                        smplx['transl'].append(gt_smplx['transl'])
                        smplx['left_hand_pose'].append(
                            gt_smplx['left_hand_pose'])
                        smplx['right_hand_pose'].append(
                            gt_smplx['right_hand_pose'])
                        smplx['jaw_pose'].append(gt_smplx['jaw_pose'])
                        smplx['leye_pose'].append(gt_smplx['leye_pose'])
                        smplx['reye_pose'].append(gt_smplx['reye_pose'])
                        smplx['expression'].append(gt_smplx['expression'])
                    else:
                        # obtain smpl data
                        gt_smpl_path = os.path.join(
                            dataset_path, df.iloc[idx]['gt_path_smpl'][pidx])
                        gt_smpl_path = gt_smpl_path.replace('.obj', '.pkl')
                        gt_smpl = pickle.load(open(gt_smpl_path, 'rb'))

                        smpl['body_pose'].append(gt_smpl['body_pose'].reshape(
                            (21, 3)))
                        smpl['global_orient'].append(gt_smpl['global_orient'])
                        smpl['betas'].append(gt_smpl['betas'])
                        smpl['transl'].append(gt_smpl['transl'])

        # change list to np array
        if self.fit == 'smplx':
            smplx['body_pose'] = np.array(smplx['body_pose']).reshape(
                (-1, 21, 3))
            smplx['global_orient'] = np.array(smplx['global_orient']).reshape(
                (-1, 3))
            smplx['betas'] = np.array(smplx['betas']).reshape((-1, 10))
            smplx['transl'] = np.array(smplx['transl']).reshape((-1, 3))
            smplx['left_hand_pose'] = np.array(
                smplx['left_hand_pose']).reshape((-1, 15, 3))
            smplx['right_hand_pose'] = np.array(
                smplx['right_hand_pose']).reshape((-1, 15, 3))
            smplx['expression'] = np.array(smplx['expression']).reshape(
                (-1, 10))
            smplx['leye_pose'] = np.array(smplx['leye_pose']).reshape((-1, 3))
            smplx['reye_pose'] = np.array(smplx['reye_pose']).reshape((-1, 3))
            smplx['jaw_pose'] = np.array(smplx['jaw_pose']).reshape((-1, 3))
        else:
            smpl['body_pose'] = np.array(smpl['body_pose']).reshape(
                (-1, 21, 3))
            smpl['global_orient'] = np.array(smpl['global_orient']).reshape(
                (-1, 3))
            smpl['betas'] = np.array(smpl['betas']).reshape((-1, 10))
            smpl['transl'] = np.array(smpl['transl']).reshape((-1, 3))

        meta['gender'] = np.array(meta['gender'])
        meta['age'] = np.array(meta['age'])
        meta['kid'] = np.array(meta['kid'])
        meta['occlusion'] = np.array(meta['occlusion'])
        meta['ethnicity'] = np.array(meta['ethnicity'])

        keypoints2d_ = np.array(keypoints2d_).reshape((-1, 127, 3))
        keypoints2d_, mask = convert_kps(keypoints2d_, 'agora',
                                         'human_data_1.0')

        keypoints3d_ = np.array(keypoints3d_).reshape((-1, 127, 4))
        keypoints3d_, _ = convert_kps(keypoints3d_, 'agora', 'human_data_1.0')

        total_dict['image_path'] = image_path_
        total_dict['bbox_xywh'] = bbox_xywh_
        total_dict['keypoints2d'] = keypoints2d_
        total_dict['keypoints3d'] = keypoints3d_
        total_dict['mask'] = mask
        total_dict['meta'] = meta
        total_dict['config'] = 'agora'
        if self.fit == 'smplx':
            total_dict['smplx'] = smplx
        else:
            total_dict['smpl'] = smpl

        # store data
        if not os.path.isdir(out_path):
            os.makedirs(out_path)

        file_name = 'agora_{}.npz'.format(mode)
        out_file = os.path.join(out_path, file_name)
        np.savez_compressed(out_file, **total_dict)
