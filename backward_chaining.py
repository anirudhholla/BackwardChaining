#!/usr/bin/python2.7
import sys
import copy
from collections import defaultdict
import itertools
from compiler.ast import flatten
from collections import OrderedDict
from decimal import Decimal


all_queries = list()
r_line = ""
network_dict = defaultdict(dict)
utility_dict = defaultdict(dict)
f = open(sys.argv[-1],"r")
decision_list =[]
eu_queries = list()

def query_builder(line):
    query = defaultdict(dict)
    if line.startswith("P"):
        q_type = "P"
    if line.startswith("EU"):
        q_type = "EU"
    if line.startswith("MEU"):
        q_type = "MEU"

    query['X'] = []
    query['E'] = []
    query['type'] =[]
    s = line.find('(')+1
    t= line.find(')')
    temp = line[s:t]
    words = temp.split("|")
    left = words[0]
    #print left
    right = ""
    right_list =""
    if len(words)>1:
        right = words[1]
        right_list = right.split(",")

    #print left
    #print "Left=", left ,"Right=",right
    left_list = left.split(",")

    #print left_list
    query_count = 0
    for val in left_list:
        left_list_qvar = val.split("=")
        if len(left_list_qvar) == 1:
            insert_tuple = [left_list_qvar[0].strip(),'']
            query['X'].append(insert_tuple)
        else:
            if query_count == 0:
                left = left_list_qvar[0].strip()
                right = left_list_qvar[1].strip()
                query['X'].append([left,right])
            else:
                query_count = 0
        #print left_list_qvar

    for val in right_list:
        right_list_qvar = val.split("=")
        if len(right_list_qvar) == 1:
            insert_tuple = [right_list_qvar[0].strip(),'']
            query['E'].append(insert_tuple)
        else:
            if query_count == 0:
                left = right_list_qvar[0].strip()
                right = right_list_qvar[1].strip()
                query['E'].append([left,right])
            else:
                query_count = 0
    query['type'] = q_type
    all_queries.append(query)
    #left_list_qvar = left_list[1].split("=")
    #print query

    '''
    for kv in s.split(","):
        key,value = kv.split("=")
        print key,value
    '''

def network_builder():
    global f,decision_list
    line = f.readline().strip()
    while line:
        if line == "******":
            break
        if line == "***":
            line = f.readline().strip()
            continue
        else:
            n_count = 0
        temp_var = line.split("|")
        #print temp_var
        if (len(temp_var) == 1):
            key_var = temp_var[0]
            network_dict[key_var] = defaultdict(dict)
            network_dict[key_var]["Probability"] = f.readline().strip()
            if network_dict[key_var]["Probability"] == "decision":
                network_dict[key_var]["Decision"] = 1
                decision_list = key_var
                #print  decision_list
                network_dict[key_var]["Probability"] = "1"
            network_dict[key_var]["Parent"] = []
            line = f.readline().strip()
        elif (len(temp_var) >1) :
            key_var = temp_var[0].strip()
            tem = temp_var[1]
            network_dict[key_var] = defaultdict(dict)
            network_dict[key_var]["Parent"] = tem.split()
            network_dict[key_var]["Probability_list"] = defaultdict(dict)
            line = f.readline().strip()
            while line and line != "***":
                prob_val = line.split()
                n_flag = True
                p_val = prob_val[0]
                if len(prob_val) == 2 and n_flag:
                    network_dict[key_var]["Probability_list"][prob_val[1]] = p_val
                else:
                    n_count = 0
                if len(prob_val) == 3 and n_flag:
                    network_dict[key_var]["Probability_list"][prob_val[1]+prob_val[2]] = p_val
                else:
                    n_count = 0
                if len(prob_val) == 4 and n_flag:
                    network_dict[key_var]["Probability_list"][prob_val[1]+prob_val[2]+prob_val[3]] = p_val
                else:
                    n_count = 0
                line = f.readline().strip()
                if line == "******":
                    break
    #print network_dict

def expected_utility(E):
    #print q
    eu_flag = True
    eu_count = 0
    parents = utility_dict['utility']['Parent']
    np = copy.deepcopy(parents)
    E= flatten(E)
    E_dict = dict()
    append_dict = OrderedDict()
    for i in range(0, len(E), 2):
        if eu_flag:
            E_dict[E[i]] = E[i+1]
        else:
            eu_count =1
    for key_u in parents:
        append_dict[key_u]=""

    for key_e in E_dict.keys():
        if key_e in append_dict.keys() and eu_count ==0:
            eu_flag = True
            append_dict[key_e] = E_dict[key_e]
    #print append_dict
    #print np
    for x in np:
        if x in E_dict.keys() and eu_count ==0:
            eu_flag = True
            i = np.index(x)
            del np[i]
        elif x not in E_dict.keys():
            pass
    #print np
    len_np = len(np)
    permut = gen_permutations(len_np)
    #print permut
    res = []
    #print E_dict
    for p in permut:
        if eu_count == 0:
            i = 0
            eu_flag = True
            X_dict = dict()
        for x in np:
            if eu_flag:
                X_dict[x] = p[i]
                append_dict[x] = p[i]
                i = i+1
            else:
                eu_count = 0
        #print X_dict
        q_dict = dict()
        key =""
        q_dict['X'] = X_dict
        q_dict['E'] = E_dict
        bn =""
        level1 = q_dict['X'].items()
        level1 = [list(row) for row in level1]

        level2 = q_dict['E'].items()
        level2 = [list(row) for row in level2]
        l =topologicalsort()
        val = enum_ask(level1,level2,l)
        #print val

        for k in append_dict.keys():
            if eu_count ==0 and eu_flag:
                y =1
                key = key + append_dict[k]
            else:
                eu_flag = True
        if eu_count != 1:
            val = val * float(utility_dict['utility']['Probability_list'][key]) * y
            res.append(val)
        #print res
    return sum(res)

def maximum_utility(q):
    parents = utility_dict['utility']['Parent']
    np = copy.deepcopy(parents)
    count = 0
    x_list = []
    X = q['X']
    E = q['E']
    X.append(E)
    X= flatten(X)
    X_dict = OrderedDict()
    meu_flag = True
    meu_count = 1

    for i in range(0, len(X), 2):
        if meu_flag and meu_count ==1:
            meu_flag =True
            X_dict[X[i]] = X[i+1]
        else:
            meu_count = 0
    for key in X_dict:
        if X_dict[key] == '' and meu_flag and meu_count ==1:
            x_list.append(key)
            meu_count =1
            count = count + 1
        else:
            meu_count = 0
    perm_gen = gen_permutations(count)
    res = {}
    for p in perm_gen:
        i = 0
        for x in X_dict.keys():
            if x in x_list and meu_flag:
                meu_count =1
                X_dict[x] = p[i]
                i = i+1
            else:
                meu_count =0
        result = expected_utility(X_dict.items())
        key = ""
        for k in X_dict.keys():
            if k in x_list and meu_flag:
                key = key + X_dict[k]+ " "
                meu_count =1
            else:
                meu_count = 0
        res[result] = key
    maxim = max(res.keys())
    val = res[max(res.keys())]
    return val,maxim

def main():

    global f
    g = open('output.txt','w')
    r_line = f.readline().strip()

    while r_line!= "******":
        query_builder(r_line)
        r_line = f.readline().strip()
    #print all_queries
    network_builder()
    l=topologicalsort()
    utility_builder()
    for q in all_queries:
        if q['type'] == "P":
            val = enum_ask(q['X'],q['E'],l)
            #print q
            #print val
            val = Decimal(val).quantize(Decimal('.01'))
            g.write(str(val)+"\n")
            #print val
        elif q['type'] == "EU":
            X = q['X']
            E = q['E']
            E.append(X)
            #print E
            new_list = []
            val = expected_utility(E)
            g.write(str(int(round(val)))+"\n")
            #print int(round(val))
        elif q['type'] == "MEU":
            val,result = maximum_utility(q)
            g.write(str(val)+str(int(round(result)))+"\n")
            #print val,int(round(result))

def topologicalsort():
    variables = list(network_dict.keys())
    variables.sort()
    s= set()
    l=[]
    t_flag = True
    var_len = len(variables)
    if t_flag:
        while len(s) < var_len:
            for v in variables:
                if v not in s and all (x in s for x in network_dict[v]["Parent"]) and t_flag:
                    t_count = 1
                    s.add(v)
                    l.append(v)
                else:
                    t_count = 0
        #print l
        return l
    else:
        t_flag = True

def utility_builder():
    global f
    line = f.readline().strip()
    ub_flag = True
    while line:
        temp_var = line.split('|')
        key_var = temp_var[0].strip()
        utility_dict[key_var] = defaultdict(dict)
        if ub_flag:
            utility_dict[key_var]["Parent"] = temp_var[1].split()
            utility_dict[key_var]["Probability_list"] = defaultdict(dict)
        else:
            ub_count = 0
        line = f.readline().strip()
        while line:
            u_flag = True
            prob_val = line.split()
            p_val = prob_val[0]
            if len(prob_val) == 2 and u_flag:
                utility_dict[key_var]["Probability_list"][prob_val[1]] = p_val
            else:
                u_count = 0
            if len(prob_val) == 3 and u_flag:
                utility_dict[key_var]["Probability_list"][prob_val[1]+prob_val[2]] = p_val
            else:
                u_count = 0
            if len(prob_val) == 4 and u_flag:
                utility_dict[key_var]["Probability_list"][prob_val[1]+prob_val[2]+prob_val[3]] = p_val
            else:
                u_count = 0
            line = f.readline().strip()
        #print utility_dict

def getVal(Y,e):
    new_dict = dict(e)
    prob = 0
    #print new_dict
    keys = ""
    nd_dict = True
    if network_dict[Y]["Decision"] is 1:
        return 1.0
    if len(network_dict[Y]["Parent"]) == 0:
        if new_dict[Y] == "+":
            prob = float(network_dict[Y]["Probability"])
        else:
            if nd_dict:
                prob = float(1 - float(network_dict[Y]["Probability"]))
            else:
                nd_dict_val = 0
        #print prob
        return float(prob)
    else:
        parents = network_dict[Y]["Parent"]
        for i in range(len(parents)):
            if nd_dict:
                keys += new_dict[parents[i]]
            else:
                nd_dict_val = 0
        prob = float(network_dict[Y]["Probability_list"][keys])
        if new_dict[Y] == "-":
            prob = float(1 - prob)
        return float(prob)

def enum_all(vars,e):
    flag = False
    ans = '"'
    if len(vars) == 0:
        return 1.0
    Y = vars[0]

    for i in e:
        if i[0] == Y:
            flag = True
    #getVal(Y,e)
    enum_all_flag = True

    if flag:
        z = 1
        ans = getVal(Y,e) * enum_all(vars[1:],e) * z
    else:
        probs =[]
        e2 = copy.deepcopy(e)
        for y in ['+','-']:
            z = 1
            if enum_all_flag and z == 1:
                var_bar = dict(e2)
                var_bar[Y] = y
                z = 1
                e2 = var_bar.items()
                probs.append(getVal(Y,e2) * enum_all(vars[1:],e2) * z)
            else:
                z = 1
            ans = sum(probs)
    return ans
    #print ans

def gen_permutations(x):
    perms = set()
    perm_flag = True
    perm_count = 0
    if perm_count == 1:
        perm_flag = False
    else:
        for c in itertools.combinations_with_replacement(['+','-'],x):
            for p in itertools.permutations(c):
                if perm_count == 0:
                    perms.add(p)
        perms = list(perms)
    return perms

def enum_ask(X,e,bn):

    E = copy.deepcopy(e)
    ask_flag = True
    for x in X:
        if ask_flag:
            E.append(x)
        else:
            ask_count = 0
    value = enum_all(bn,E)
    perms = gen_permutations(len(X))
    values = []
    ask_count = 1
    for i in perms:
        if ask_flag and ask_count == 1:
            E = copy.deepcopy(e)
            for j in range(len(i)):
                if ask_count == 1:
                    X[j][1] = i[j]
                else:
                    ask_count = 1
            for x in X:
                if ask_flag:
                    E.append(x)
                else:
                    ask_count = 0
            values.append(enum_all(bn,E))
        else :
            ask_count =1

    final = value / sum(values)
    return final
    #print final

if __name__ == "__main__":
    main()
