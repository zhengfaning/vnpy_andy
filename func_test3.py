#Creating line plots using NumPy arrays
#Import required packages
import numpy as np
import random
# from bokeh.io import output_file, show
# from bokeh.plotting import figure

#Creating an array for the points along the x and y axes
array_x =np.array([1,2,3,4,5,6,8,90,86,84,83,67,70,71,89,91,64,83])
array_y = np.array([5,6,7,8,9,10])
xx = [1,5,6,7,6,8]


def calc(array):
    v_list = []
    p_list = []
    # r = array[::-1]
    r = array
    l = len(array) - 1
    param = 2
    now = r[0]
    pos = 1
    x = 0
    start_pos = 0
    positive_pos = None
    negative_pos = None
    vol = 0
    u_vol = 0
    d_vol = 0
    while pos < l:
        n_vol = r[pos] - now
        vol += r[pos] - now
        u_vol = u_vol + n_vol
        if u_vol < 0:
            u_vol = 0
        d_vol = d_vol + n_vol
        if d_vol > 0:
            d_vol = 0
        if now < r[pos]:

            if x < param:
                # n_vol = r[pos] - now  
                # vol += n_vol
                x = 1 if x < 0 and r[pos] > r[start_pos] else x + 1
                print("x+, x = {0}".format(x))
            else:
                positive_pos = pos
                print("positive_pos = {0}".format(positive_pos))
                    
        elif now > r[pos]:
            if x > -param:

                x = -1 if x > 0 and r[pos] < r[start_pos] else x - 1
                print("x-, x = {0}".format(x))
            else:
                negative_pos = pos
                print("negative_pos = {0}".format(negative_pos))
        print("now = {}, new = {}, vol = {:.2%},u_vol = {},d_vol = {},".format(
            now, r[pos], vol/r[start_pos], u_vol, d_vol))

        if x == 0:
            if not positive_pos is None:
                u_vol = 0
                d_vol = 0
                maxval = np.max(r[positive_pos:pos+1])
                if maxval > r[positive_pos]:
                    positive_pos = pos
                    x += 1
                else:
                    max_val = np.max(r[start_pos:positive_pos + 1])
                    t_pos = np.argmax(r[start_pos:positive_pos + 1])
                    t_pos += start_pos
                    v_list.append(max_val)
                    p_list.append(t_pos)
                    start_pos = positive_pos
                    positive_pos = None
                    x = -param
                    negative_pos = pos
            elif not negative_pos is None:
                u_vol = 0
                d_vol = 0
                minval = np.min(r[negative_pos:pos+1])
                if minval < r[negative_pos]:
                    negative_pos = pos
                    x -= 1
                else:
                    min_val = np.min(r[start_pos:negative_pos + 1])
                    t_pos = np.argmin(r[start_pos:negative_pos + 1])
                    t_pos += start_pos
                    v_list.append(min_val)
                    p_list.append(t_pos)
                    start_pos = negative_pos
                    negative_pos = None
                    x = param
                    positive_pos = pos
        now = r[pos]
        pos += 1

    print(v_list)
    print(p_list)

    return v_list, p_list
    

def calc1(array):
    v_list = []
    p_list = []
    # r = array[::-1]
    r = array
    l = len(array) - 1
    param = 3
    now = r[0]
    pos = 1
    x = 0
    start_pos = 0
    positive_pos = None
    negative_pos = None
    while pos < l:
        print("now = {}, new = {}".format(now, r[pos]))
        if now < r[pos]:
            if x < param:
                x = 1 if x < 0 and r[pos] > r[start_pos] else x + 1
                print("x+, x = {0}".format(x))
            else:
                positive_pos = pos
                print("positive_pos = {0}".format(positive_pos))
                    
        elif now > r[pos]:
            if x > -param:
                x = -1 if x > 0 and r[pos] < r[start_pos] else x - 1
                print("x-, x = {0}".format(x))
            else:
                negative_pos = pos
                print("negative_pos = {0}".format(negative_pos))
        if x == 0:
            if not positive_pos is None:
                maxval = np.max(r[positive_pos:pos+1])
                if maxval > r[positive_pos]:
                    positive_pos = pos
                    x += 1
                else:
                    max_val = np.max(r[start_pos:positive_pos + 1])
                    t_pos = np.argmax(r[start_pos:positive_pos + 1])
                    t_pos += start_pos
                    v_list.append(max_val)
                    p_list.append(t_pos)
                    start_pos = positive_pos
                    positive_pos = None
                    x = -param
                    negative_pos = pos
            elif not negative_pos is None:
                minval = np.min(r[negative_pos:pos+1])
                if minval < r[negative_pos]:
                    negative_pos = pos
                    x -= 1
                else:
                    min_val = np.min(r[start_pos:negative_pos + 1])
                    t_pos = np.argmin(r[start_pos:negative_pos + 1])
                    t_pos += start_pos
                    v_list.append(min_val)
                    p_list.append(t_pos)
                    start_pos = negative_pos
                    negative_pos = None
                    x = param
                    positive_pos = pos
        now = r[pos]
        pos += 1

    print(v_list)
    print(p_list)

    return v_list, p_list


# pp = np.argmin(array_x)
# print(array_x[pp])
# xp = np.where(array_x==np.max(array_x))
# print(array_x[xp[0]])
# calc1(array_x)