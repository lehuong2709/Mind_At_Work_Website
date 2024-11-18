import gurobipy as gp
from gurobipy import GRB
import numpy as np


def facility_location(points, urban_points, groups, pairwise_distances, existing_facilities, existing_distances, k, p=2,
                      urban_weight=5, verbose=False, optimality_tol=None):
    """
    points: list of points
    pairwise_distances: dictionary of pairwise distances between points
        not all distances have to be included
    existing_facilities: list of existing existing_facilities among points
    existing_distances: dictionary of distances from each point to the closest existing facility,
        these distances are used to determine the closest facility to each point
    k: number of existing_facilities to locate

    returns: list of existing_facilities
    """
    points_plus_one = points + ['existing']
    for j in points:
        pairwise_distances[j]['existing'] = existing_distances[j]

    model = gp.Model('facility_location')
    model.setParam('OutputFlag', 0)

    Y = {}
    for i in points_plus_one:
        Y[i] = model.addVar(vtype=GRB.CONTINUOUS, lb=0, ub=1, name=f'Y_{i}')
        if i in existing_facilities:
            model.addConstr(Y[i] == 1)
    model.addConstr(Y['existing'] == 1)
    model.addConstr(gp.quicksum(Y[i] for i in points) == k + len(existing_facilities))

    X = {j: {} for j in points}
    W = model.addVars(points, name='W', vtype=GRB.CONTINUOUS)
    for j in points:
        for i in pairwise_distances[j].keys():
            X[j][i] = model.addVar(vtype=GRB.CONTINUOUS, name=f'X_{j}_{i}', lb=0)
            model.addConstr(X[j][i] <= Y[i])
        model.addConstr(gp.quicksum(X[j][i] for i in points_plus_one if i in pairwise_distances[j].keys()) == 1)
        if j in urban_points:
            model.addConstr(W[j] == urban_weight * gp.quicksum(pairwise_distances[j][i] * X[j][i] for i in points_plus_one if i in pairwise_distances[j].keys()))
        else:
            model.addConstr(W[j] == gp.quicksum(pairwise_distances[j][i] * X[j][i] for i in points_plus_one if i in pairwise_distances[j].keys()))

    r = len(groups)
    Z = model.addVars(r, name='Z', vtype=GRB.CONTINUOUS)
    for s in range(r):
        group = groups[s]
        model.addConstr(Z[s] == gp.quicksum(W[j] for j in group)/len(group))

    t = model.addVar(vtype=GRB.CONTINUOUS, name='t')
    if p == 1 or p == 2:
        model.addConstr(t == gp.norm(Z, p))
    else:
        for s in range(r):
            model.addConstr(Z[s] <= t)

    if optimality_tol is not None:
        model.setParam('OptimalityTol', optimality_tol)

    model.setParam('OutputFlag', verbose)
    model.update()
    model.setObjective(t, GRB.MINIMIZE)
    model.optimize()

    W = {key: W[key].x for key in W.keys()}
    X = {j: {key: X[j][key].x for key in X[j].keys()} for j in points}
    Y = {key: Y[key].x for key in Y.keys()}
    Z = {key: Z[key].x for key in Z.keys()}

    return W, X, Y, Z, model


def filter_small_values(A, distances, alpha):
    """
    Test function for filter_small_values
    :param A: matrix of nonnegative values
    :param distances: matrix of nonnegative distances
    :param alpha: parameter in (0, 1]
    :return: filtered matrix
    """
    sorted_distances = sorted(distances.items(), key=lambda x: x[1])
    B = {}

    sum_of_A_values = 0
    while sum_of_A_values < alpha:
        index = sorted_distances.pop(0)[0]
        sum_of_A_values += A[index]
        B[index] = A[index]

    indices = list(B.keys())
    for index in indices:
        B[index] = B[index]/sum_of_A_values
        if B[index] < 0.001:
            del B[index]

    return B


def find_facility(X, pairwise_distances, unassigned_clients):
    """
    Finds a facility location given the facility location variables X and Y
    :param X: facility location variables
    :param Y: facility location variables
    :return: a facility location
    """
    neighbors = {}

    for j in unassigned_clients:
        neighbors[j] = {i for i in X[j].keys() if X[j][i] >= 0.001}

    j_star = -1
    # i_star = -1
    current_min_max = np.inf
    for j in unassigned_clients:
        i = sorted(neighbors[j], key=lambda i: pairwise_distances[j][i])[0]
        farthest_distance_for_j = pairwise_distances[j][i]
        if farthest_distance_for_j < current_min_max:
            j_star = j
            # i_star = i
            current_min_max = farthest_distance_for_j

    degrees = {i: 0 for i in X[j_star].keys()}
    for j in unassigned_clients:
        for i in X[j].keys():
            if i in X[j_star].keys() and X[j][i] >= 0.001:
                degrees[i] += 1
    # Choose the max-degree facility
    i_star = max(degrees, key=degrees.get)

    return i_star, j_star


def round_lp_solution(points, X, Y, pairwise_distances, k, alpha=0.5, existing_facilities=None):
    if 'existing' not in existing_facilities:
        existing_facilities.append('existing')

    new_facilities = set()
    # for i in points:
    #     if Y[i] >= 0.999:
    #         new_facilities.add(i)
            # if i not in existing_facilities:
            #     existing_facilities.append(i)

    unassigned_clients = points.copy()      # Set of unassigned clients
    for j in points:
        # if X[j]['existing'] >= 0.01:
        #     unassigned_clients.remove(j)
        #     break
        closest_facility = -1
        closest_distance = np.inf
        for i in X[j].keys():
            if X[j][i] >= 0.01:
                if pairwise_distances[j][i] < closest_distance:
                    closest_distance = pairwise_distances[j][i]
                    closest_facility = i
        if closest_facility in existing_facilities:
            unassigned_clients.remove(j)

    X1 = {}
    for j in points:
        X1[j] = filter_small_values(X[j], pairwise_distances[j], alpha)

    while len(unassigned_clients) > 0 and len(new_facilities) < k:
        i_star, j_star = find_facility(X1, pairwise_distances, unassigned_clients)
        if i_star != 'existing':
            new_facilities.add(i_star)
        clients_to_remove = set()
        for j in unassigned_clients:
            for i in X1[j].keys():
                if i in X1[j_star].keys() and X1[j_star][i] >= 0.001 and X1[j][i] >= 0.001:
                    clients_to_remove.add(j)

        for j in clients_to_remove:
            unassigned_clients.remove(j)

    if len(new_facilities) < k:
        facilities_sorted = sorted(Y.keys(), key=lambda i: Y[i])
        for i in facilities_sorted:
            if i not in existing_facilities:
                new_facilities.add(i)
                if len(new_facilities) == k:
                    break

    existing_facilities.remove('existing')

    return new_facilities
