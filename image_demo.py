import cv2
import time
import argparse
import os
import torch

import json

import posenet


parser = argparse.ArgumentParser()
parser.add_argument('--model', type=int, default=101)
parser.add_argument('--scale_factor', type=float, default=1.0)
parser.add_argument('--notxt', action='store_true')
parser.add_argument('--image_dir', type=str, default='./images')
parser.add_argument('--output_dir', type=str, default='./output')
args = parser.parse_args()


def main():
    model = posenet.load_model(args.model)
    #model = model.cuda()
    output_stride = model.output_stride

    if args.output_dir:
        if not os.path.exists(args.output_dir):
            os.makedirs(args.output_dir)

    filenames = [
        f.path for f in os.scandir(args.image_dir) if f.is_file() and f.path.endswith(('.png', '.jpg', '.jpeg'))]

    start = time.time()
    for f in filenames:
        input_image, draw_image, output_scale = posenet.read_imgfile(
            f, scale_factor=args.scale_factor, output_stride=output_stride)

        with torch.no_grad():
            input_image = torch.Tensor(input_image)#.cuda()

            heatmaps_result, offsets_result, displacement_fwd_result, displacement_bwd_result = model(input_image)

            pose_scores, keypoint_scores, keypoint_coords = posenet.decode_multiple_poses(
                heatmaps_result.squeeze(0),
                offsets_result.squeeze(0),
                displacement_fwd_result.squeeze(0),
                displacement_bwd_result.squeeze(0),
                output_stride=output_stride,
                max_pose_detections=10,
                min_pose_score=0.20)

        keypoint_coords *= output_scale

        if args.output_dir:
            draw_image = posenet.draw_skel_and_kp(
                draw_image, pose_scores, keypoint_scores, keypoint_coords,
                min_pose_score=0.20, min_part_score=0.20)

            cv2.imwrite(os.path.join(args.output_dir, os.path.relpath(f, args.image_dir)), draw_image)

        if not args.notxt:
            print()
            datos_pose_imagen = dict()
            datos_pose_imagen['image'] = f

            print("Results for image: %s" % datos_pose_imagen['image'])
            for pi in range(len(pose_scores)):
                if pose_scores[pi] == 0.:
                    break
                print('Pose #%d, score = %f' % (pi, pose_scores[pi]))

                puntos = dict()
                listado_puntos_pose = list()
                for ki, (s, coordenadas) in enumerate(zip(keypoint_scores[pi, :], keypoint_coords[pi, :, :])):
                    key_point_pose = dict()
                    key_point_pose["part"] = posenet.PART_NAMES[ki]
                    key_point_pose["score"] = s

                    position = dict()
                    position['x'] = coordenadas[0]
                    position['y'] = coordenadas[1]
                    key_point_pose["position"] = position

                    listado_puntos_pose.append(key_point_pose)
                    #print('Keypoint %s, score = %f, coord = %s' % (posenet.PART_NAMES[ki], s, coordenadas))
                puntos["keypoints"] = listado_puntos_pose
                puntos["score"] = pose_scores[pi]

                datos_pose_imagen[str(pi)] = puntos

                nameFile = "." + os.path.join(args.output_dir, os.path.relpath(f, args.image_dir)).split(".")[1] + ".json"
                with open(nameFile, 'w', encoding='utf-8') as outfile:
                    json.dump(datos_pose_imagen, outfile, ensure_ascii=False, indent=4)


    print('Average FPS:', len(filenames) / (time.time() - start))


if __name__ == "__main__":
    main()
