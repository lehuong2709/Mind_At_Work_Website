"""
This script contains functions for plotting the state map and pharmacies in the given state or county.
Author: Jai Moondra
"""
import plotly.express as px
import pandas as pd
import json
import matplotlib.pyplot as plt
import scripts.utils as utils
from pathlib import Path
from scripts.constants import *
import os


boundary_data_path = './data/usa_state_boundaries.json'


def plot_state_map(state_name='Georgia'):
    """
    Plots the state map for the given state name
    :param state_name: name of the state
    :return:
    """
    df = pd.read_json(boundary_data_path)

    for i in range(len(df.index)):
        if df.iloc[i]['features']['properties']['NAME'] == state_name:
            coordinates = df.iloc[i]['features']['geometry']['coordinates']

    if len(coordinates) == 1:
        coordinates = coordinates[0]
        boundary_longitudes = []
        boundary_latitudes = []
        for i in range(len(coordinates)):
            boundary_longitudes.append(coordinates[i][0])
            boundary_latitudes.append(coordinates[i][1])

        ax = plt.gca()
        ax.set_aspect(aspect_ratio)
        plt.plot(boundary_longitudes, boundary_latitudes, linewidth=1, color='gray')
        # plt.legend([state_name], loc='best')

    else:
        for i in range(len(coordinates)):
            boundary_longitudes = []
            boundary_latitudes = []
            for j in range(len(coordinates[i][0])):
                boundary_longitudes.append(coordinates[i][0][j][0])
                boundary_latitudes.append(coordinates[i][0][j][1])

            ax = plt.gca()
            ax.set_aspect(aspect_ratio)
            plt.plot(boundary_longitudes, boundary_latitudes, linewidth=1, color='gray')
            # plt.legend([state_name], loc='best')
    return


def plot_pharmacies(state_name='Georgia', which='all', county_name=None, loc='best'):
    """
    Plots the pharmacies in the given state or county
    :param state_name: name of the state
    :param which:
    :param county_name:
    :param loc:
    :return:
    """
    if county_name is not None:
        county_name = county_name.upper()
    if which == 'all':
        k, pharmacy_coordinates = utils.get_pharmacy_coordinates(state_name=state_name, which='all', county_name=county_name)

        plt.scatter(*zip(*pharmacy_coordinates), marker='x', s=5, label='Pharmacy')
        ax = plt.gca()

        plt.xlabel('Longitude')
        plt.ylabel('Latitude')
        ax.set_aspect(aspect_ratio)
    elif which == 'top3':
        k, cvs_pharmacy_coordinates, walgreens_pharmacies_coordinates, walmart_pharmacies_coordinates =(
            utils.get_pharmacy_coordinates(state_name=state_name, which='top3', county_name=county_name))
        plt.scatter(*zip(*walmart_pharmacies_coordinates), color='orange', marker='x', s=7, label='Walmart', alpha=0.9)
        plt.scatter(*zip(*cvs_pharmacy_coordinates), color='red', marker='x', s=7, label='CVS', alpha=0.85)
        plt.scatter(*zip(*walgreens_pharmacies_coordinates), color='green', marker='x', s=7, label='Walgreens', alpha=0.8)

        ax = plt.gca()

        # plt.legend(['CVS', 'Walgreens', 'Walmart'], loc=loc)
        plt.legend(loc=loc)
        plt.xlabel('Longitude')
        plt.ylabel('Latitude')
        ax.set_aspect(aspect_ratio)

    else:
        raise ValueError('which must be either "all" or "top3"')

    return k
