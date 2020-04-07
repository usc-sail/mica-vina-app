import os, sys


def cluster_segments(gender_write_path):
    male_file = os.path.join(gender_write_path, 'male.ts')
    female_file = os.path.join(gender_write_path, 'female.ts')

    data = {}
    data['male'] = [x.rstrip().split() for x in open(male_file, 'r').readlines()]
    data['female'] = [x.rstrip().split() for x in open(female_file, 'r').readlines()]

    file_id = data['male'][0][1]
    data['male'] = [[x[0], x[1], float(x[2]), float(x[3])] for x in data['male']]
    data['female'] = [[x[0], x[1], float(x[2]), float(x[3])] for x in data['female']]

    seg_data = []
    for gen in ['male', 'female']:
        write_file = os.path.join(gender_write_path, gen+'_resegmented.ts')
        idx = 0
        with open(write_file, 'w') as fw:
            while idx < len(data[gen]):
                start = data[gen][idx][-2]
                end = data[gen][idx][-1]
                if idx != len(data[gen])-1:
                    while data[gen][idx+1][-2] == data[gen][idx][-1]:
                        idx += 1
                        end = data[gen][idx][-1]    
                        if idx == len(data[gen])-1:
                            break
                seg_start = str(int(1e10*start))[:8]
                seg_end   = str(int(1e10*end))[:8]
                seg_data.append([start, end, gen])
                seg_id = file_id + '_' + seg_start + '_' + seg_end
                fw.write('{}\t{}\t{}\t{}\n'.format(seg_id, file_id, start, end))
                idx += 1

    ts_file = os.path.join(gender_write_path, file_id + '.ts')
    csv_file = os.path.join(gender_write_path, file_id + '.csv')

    sorted_seg_data = sorted(seg_data)
    with open(ts_file, 'w') as fw:
        fw.write("Start(s)\tEnd(s)\tGender\n")
        for segment in sorted_seg_data:
            fw.write('{}\t{}\t{}\n'.format(segment[0], segment[1], segment[2]))

    with open(csv_file, 'w') as fw:
        fw.write("Start(s),End(s),Gender\n")
        for segment in sorted_seg_data:
            fw.write('{},{},{}\n'.format(segment[0], segment[1], segment[2]))

if __name__ == '__main__':
    gender_write_path = sys.argv[1]
    cluster_segments(gender_write_path)
