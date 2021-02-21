#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Feb  6 13:14:20 2021

@author: Steven Charles-Mindoza
"""

import pandas as pd
import os
from matplotlib import pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.colors import to_rgb
from matplotlib import colors
from astropy.timeseries import LombScargle
from astropy import units as u
import numpy as np
import matplotlib as mpl
import seaborn as sns
mpl.rcParams['figure.dpi'] = 300

base_context = {

                "font.size": 18,
                "axes.labelsize": 18,
                "axes.titlesize": 14,
                "xtick.labelsize": 16,
                "ytick.labelsize": 16,
                "legend.fontsize": 16,

                "axes.linewidth": 1.25,
                "grid.linewidth": 1,
                "lines.linewidth": 1.5,
                "lines.markersize": 6,
                "patch.linewidth": 1,

                "xtick.major.width": 0,
                "ytick.major.width": 0,
                "xtick.minor.width": 0,
                "ytick.minor.width": 0,

                "xtick.major.size": 0,
                "ytick.major.size": 0,
                "xtick.minor.size": 0,
                "ytick.minor.size": 0,

                }

sns.set_theme(style="whitegrid")
sns.set_context('paper')
sns.set_palette('deep')

def change_width(ax, new_value):
    for patch in ax.patches:
        current_width = patch.get_width()
        diff = current_width - new_value
        patch.set_width(new_value)
        patch.set_x(patch.get_x() + diff * .5)


def plot_epoch(sub=False):
    sns.set_theme(style="whitegrid", rc = base_context)
    if sub==True:
        fig, ax = plt.subplots(figsize=(20,25))
    archive_list = ['eu', 'nasa', 'org', 'all']
    for i, archive in enumerate(archive_list):
        here = os.path.dirname(os.path.abspath(__file__))
        df = pd.read_csv(f'{here}/data/Targets/{archive}_tess_viable.csv') \
        .sort_values('Epochs', ascending=False).reset_index(drop=True)
        # df = pd.read_csv(f'Targets/{archive}_tess_viable.csv') \
        # .sort_values('Epochs', ascending=False).reset_index(drop=True)
        # candidates = f'{len(df)} {archive.upper()} Archive ' +\
        #            'Candidates Ranked by Epoch Count ' +\
        #             f"({df['Epochs'].sum()} Total)"
        candidates = f'{len(df)} {archive.upper()} Archive ' +\
             'Candidates Ranked by Descending Observed Transits'
        df[candidates] = 1
        df['Candidate Cumsum'] = df[candidates].cumsum()
        total_candidates = df[candidates].sum()
        df['Candidate Frequency'] = df['Candidate Cumsum'] / total_candidates
        
        df['Epoch Cumsum'] = df['Epochs'].cumsum()
        total_epochs = df['Epochs'].sum()
        df['Epoch Frequency'] = df['Epoch Cumsum'] / total_epochs
        # highlights = df.groupby('Frequency')['Exoplanet', 'Epochs']
        # .agg({'Exoplanet':'count','Epochs':'sum'})

        highlights = df.groupby(pd.cut(df["Epoch Frequency"],
                                       np.arange(0, 1.0+0.1, 0.1))).sum()
        cumsum_cand = highlights[candidates].cumsum()
        cumsum_epochs = highlights['Epochs'].cumsum()
        if sub==False:
            fig, ax = plt.subplots(figsize=(15,45))
            sns.despine(fig=fig, ax=ax)
        temp = 411 + i
        ax=plt.subplot(temp)
        [ax.axvline(x=i+0.4, color='k', marker=',',
                    alpha=0.5, ymin=0,ymax=0.15) for i in range(10)]
        [ax.axvline(x=i+0.45, color='k', marker=',',
                    alpha=0.5, ymin=0.8,ymax=1) for i in range(10)]
        # [ax.text(i+0.34,total_epochs/47,
        #          f"{i+1}0% - {cumsum_cand[i]} Candidates - {cumsum_epochs[i]} Transits",rotation=90)
        #          for i in range(10)]
        [ax.text(i+0.34,total_epochs/47,
                 f"{i+1}0% of All Transits - {round(cumsum_cand[i]*100/total_candidates)}% Candidates",rotation=90)
                 for i in range(10)]
        [ax.text(i-0.1, highlights['Epochs'][i] + 5,
                 str(highlights[candidates][i]),rotation=0) for i in range(10)]
        # Top Planets
        twenty_perc = cumsum_cand[2]
        textstr = '\n'.join(df['Exoplanet'][0:twenty_perc])
        props = dict(boxstyle='round', facecolor='white', alpha=0.1)
        ax.text(1.075, 0.96, f'30% of \nAll Transits \n{twenty_perc} Candidates',
                transform=ax.transAxes, fontsize=16, weight='bold',
                verticalalignment='top', bbox=props, ha='center')
        ax.text(1.02, 0.85, textstr, transform=ax.transAxes, fontsize=16,
                verticalalignment='top', bbox=props)
        # PLOT!
        highlights['Observed Transits'] = highlights['Epochs']
        sns.barplot(ax=ax, data=highlights,
                    x=candidates, y = 'Observed Transits',
                    dodge=False, palette='rocket')
        change_width(ax, 0.6)
        # ax.get_legend().remove()
        
        ax.xaxis.tick_bottom()
        column_labels = [f'{i}0 - {i+1}0%'.replace('00 - 10%', '0 - 10%') for i in range(10)]
        ax.set_xticklabels(column_labels, minor=False)
        if sub ==False:
            plt.savefig(f'{archive}_epoch_rank.jpg', bbox_inches='tight')
    if sub==True:
        plt.savefig('epoch_rank.jpg', bbox_inches='tight')
        

def lc_plot(file, flatten=False):
    sns.set_theme(style="whitegrid", rc = base_context)
    from lightkurve import LightCurve
    df = pd.read_csv(file).dropna()
    time = df['Time'].values - 2457000
    flux = df['Flux'].values
    flux_err = df['Flux err'].values
    
    lc = LightCurve(time, flux, flux_err, time_format='btjd')
    lc = lc.remove_outliers().normalize()
    if flatten==True:
        lc = lc.remove_outliers().flatten()
    
    pg = lc.to_periodogram(oversample_factor=25)
    period = float(pg.period_at_max_power/u.d)
    pg = lc.to_periodogram(oversample_factor=25, maximum_period=period*1.25,
                           minimum_period=period*0.75)
    # PLOT!
    fig, ax = plt.subplots(figsize=(15,15))
    ax=plt.subplot(311)
    plt.errorbar(lc.time, lc.flux,
                 lc.flux_err, color='b',
                 alpha=0.2, zorder=1, capsize=2, ls='none')
    plt.scatter(lc.time, lc.flux, color='k', s=0.5, alpha=0.6, zorder=2)
    plt.xlabel('Time (BTJD)')
    plt.ylabel('Flux')
    
    ax=plt.subplot(312)
    plt.plot(pg.period, pg.power, color='k', alpha=0.8)
    plt.xlabel('Period')
    plt.ylabel('Power')
    #pg.show_properties()

    # Folded
    period = pg.period_at_max_power
    condition = (lc.flux==np.min(lc.flux))
    t0 = np.where(condition)[0][0]
    t0 = lc.time[t0]
    folded_lc = lc.fold(period=period, t0=t0)
    
    ax=plt.subplot(313)
    plt.errorbar(folded_lc.time, folded_lc.flux,
                 folded_lc.flux_err, color='b',
                 alpha=0.2, zorder=1, capsize=2, ls='none')
    plt.scatter(folded_lc.time, folded_lc.flux,
                alpha=0.4, color='k', zorder=2, s=2)
    plt.xlabel('Phase')
    plt.ylabel('Flux')
    filename = f'{file}'.replace('.csv', '')
    plt.savefig(f'{filename}.jpg', bbox_inches='tight')


def mw():
    from astropy import units as u
    import astropy.coordinates as apycoords
    from mw_plot import MWSkyMap, MWPlot
    here = os.path.dirname(os.path.abspath(__file__))
    df = pd.read_csv(f'{here}/data/Targets/nasa_tess_viable.csv')
    ra = df['RA'].values * u.deg
    dec = df['DEC'].values * u.deg
    z = df['Epochs'].values
    distance = df['Distance'] .values * u.pc
    c = apycoords.SkyCoord(ra=ra, dec=dec, distance=distance, frame='icrs')
    
    plot_instance = MWPlot(mode='face-on', center=(0, 0)*u.kpc, radius= 12*u.kpc,
                       unit=u.kpc, coord='galactic', annotation=True,  grayscale=False)
    plot_instance.fontsize = 35  # fontsize for matplotlib plotting
    plot_instance.figsize = (20, 20)  # figsize for matplotlib plotting
    plot_instance.dpi = 200  # dpi for matplotlib plotting
    plot_instance.cmap = 'hot'  # matplotlib cmap: https://matplotlib.org/examples/color/colormaps_reference.html
    #plot_instance.clim = (vmin, vmax) # colorbar range
    plot_instance.imalpha = 0.85  # alpha value for the milkyway image
    plot_instance.s = 100.0  # make the scatter points bigger
    plot_instance.tight_layout = True # whether plt.tight_layout() will be run
    
    plot_instance.mw_scatter(-c.galactic.cartesian.x,
                             c.galactic.cartesian.y, [z, 'Transits Observed'])
    plot_instance.savefig('mw_zoom_out.png')
    
    
    plot_instance = MWPlot(mode='face-on', center=(0, 0)*u.kpc, radius= 2*u.kpc,
                       unit=u.kpc, coord='galactic', annotation=True,  grayscale=False)
    plot_instance.fontsize = 35  # fontsize for matplotlib plotting
    plot_instance.figsize = (20, 20)  # figsize for matplotlib plotting
    plot_instance.dpi = 200  # dpi for matplotlib plotting
    plot_instance.cmap = 'hot'  # matplotlib cmap: https://matplotlib.org/examples/color/colormaps_reference.html
    #plot_instance.clim = (vmin, vmax) # colorbar range
    plot_instance.imalpha = 1  # alpha value for the milkyway image
    plot_instance.s = 100.0  # make the scatter points bigger
    plot_instance.tight_layout = True # whether plt.tight_layout() will be run
    
    plot_instance.mw_scatter(-c.galactic.cartesian.x,
                             c.galactic.cartesian.y, [z, 'Transits Observed'])
    plot_instance.savefig('mw.png')
    
    
    plot_instance = MWPlot(mode='face-on', center=(0, 0)*u.kpc, radius= 1*u.kpc,
                       unit=u.kpc, coord='galactic', annotation=True,  grayscale=False)
    plot_instance.fontsize = 35  # fontsize for matplotlib plotting
    plot_instance.figsize = (20, 20)  # figsize for matplotlib plotting
    plot_instance.dpi = 200  # dpi for matplotlib plotting
    plot_instance.cmap = 'hot'  # matplotlib cmap: https://matplotlib.org/examples/color/colormaps_reference.html
    #plot_instance.clim = (vmin, vmax) # colorbar range
    plot_instance.imalpha = 1  # alpha value for the milkyway image
    plot_instance.s = 100.0  # make the scatter points bigger
    plot_instance.tight_layout = True # whether plt.tight_layout() will be run
    
    plot_instance.mw_scatter(-c.galactic.cartesian.x,
                             c.galactic.cartesian.y, [z, 'Transits Observed'])
    plot_instance.savefig('mw_zoom_in.png')
    

def oc(t0, t0_err, file='Complete_Results.csv', exoplanet=None):
    path_ttv = file
    data_ttv = pd.read_csv(path_ttv).set_index('Parameter') \
                .filter(like = 't0', axis=0).drop(['Telescope', 'Filter'], axis=1)
    
    t0_o = t0 # data['Best'] .values
    t0_oerr = t0_err # data['Error'].astype(float) .values
    t0_c = data_ttv['Best'] .values
    t0_cerr = data_ttv['Error'].astype(float) .values
    epoch_no = (data_ttv['Epoch'].astype(int) + 1) . values
    
    ominusc = t0_c - t0_o
    ominuscerr = t0_cerr - t0_oerr
    ominusc *= 24 * 60
    ominuscerr *= 24 * 60
    from sklearn.preprocessing import scale
    ominusc = scale(ominusc)

    
    # Generalised Lomb Scargle Floating Mean
    ls = LombScargle(epoch_no, ominusc, ominuscerr)
    frequency, power = ls.autopower(nyquist_factor=1, samples_per_peak=100)
    
    # False Alarm Probability
    fap = ls.false_alarm_probability(power.max())
    levels = [0.99, 0.5, 0.05, 0.01]
    false_alarm_levels = ls.false_alarm_level(levels)
    pack = {'FAP':false_alarm_levels, 'Percentage':levels}
    period = 1/frequency[np.argmax(power)]
    # Get the best frequency for plotting??
    fit_x = np.linspace(epoch_no.min(), epoch_no.max(), 1000)
    fit_y = ls.model(fit_x, frequency[np.argmax(power)])
    
    
    fig, ax = plt.subplots(figsize=(15,15))
    
    ax=plt.subplot(311)
        
    # Make figure and axes
    fig = plt.figure(figsize=(12,8))
    gs = gridspec.GridSpec(2, 1)

    oc_ax = fig.add_subplot(gs[0])
    ls_ax = fig.add_subplot(gs[1])

    #Plot data
    oc_ax.errorbar(epoch_no, ominusc, ominuscerr, marker='.', 
                   elinewidth=0.8, color='dimgrey', linestyle='', 
                   capsize=2, alpha=0.8, zorder=1)
    oc_ax.scatter(epoch_no, ominusc, marker='.', color='dimgrey', zorder=2)
    oc_ax.axhline(0, color='black', linestyle='--', linewidth=1)
    oc_ax.plot(fit_x, fit_y, color='red', alpha=0.8)
    
    #ls_ax.scatter(1/frequency, power, color='dimgrey', alpha=0.1, zorder=1, s=10)
    ls_ax.plot(1/frequency, power, linestyle='-', linewidth=0.75, zorder=2,
               marker='', color='k')
    pos = len(epoch_no)*0.985
    for (level, i) in zip(false_alarm_levels, levels):
        ls_ax.axhline(level, color='r', linestyle='--', alpha=0.8)
        ls_ax.annotate(f'{str(int(i*100))}'+'$\%$',
                       (pos, level*1.018), color='k', ha='center')
    if fap > 0.5:
        pass
    else:
        ls_ax.annotate(f'Period: {int(period)}\nFAP: {fap*100:.2f}$\%$',
                        (period*1.03, power.max()*1.03), color='k', weight='bold', ha='center')
    # Sort out labels etc
    oc_ax.set_xlabel('Epoch')
    oc_ax.set_ylabel('O-C (minutes)')

    ls_ax.set_xlabel('Period (Epochs)')
    ls_ax.set_ylabel('Power')

    oc_ax.tick_params('both', which='both', direction='in', bottom=True, left=True)
    ls_ax.tick_params('both', which='both', direction='in', bottom=True, left=True)

    ls_ax.set_xscale('linear')
    ls_ax.set_xlim([0, len(epoch_no)])
    ls_ax.set_ylim([0, power.max()*1.2])
    fig.tight_layout()
    if exoplanet==None:
        fig.savefig('O-C.jpg', bbox_inches='tight')
    else:
        fig.savefig(f'firefly/{exoplanet}/O-C.jpg', bbox_inches='tight')
   
  
def oc_fold(t0, t0err, file='Complete_results.csv', exoplanet=None):
    '''
    Loads in the t0 and errors
    '''

    path_ttv = file
    data_ttv = pd.read_csv(path_ttv).set_index('Parameter') \
                .filter(like = 't0', axis=0).drop(['Telescope', 'Filter'], axis=1)
    
    t0_o = t0 #data['Best'] .values
    t0_oerr = t0err # data['Error'].astype(float) .values
    t0_c = data_ttv['Best'] .values
    t0_cerr = data_ttv['Error'].astype(float) .values
    epoch_no = (data_ttv['Epoch'].astype(int) + 1) . values
    
    ominusc = t0_c  - t0_o
    ominuscerr = t0_cerr - t0_oerr
    ominusc *= 24 * 60
    ominuscerr *= 24 * 60
    from sklearn.preprocessing import scale
    ominusc = scale(ominusc)
    
    
    # Do the Lomb-Scargel stuff.
    ls = LombScargle(epoch_no, ominusc, ominuscerr)

    #frequency, power = ls.autopower(minimum_frequency=1/200, maximum_frequency=1/100)
    frequency, power = ls.autopower(nyquist_factor=1, samples_per_peak=100)
    best_f = frequency[np.argmax(power)]
    best_P = 1/frequency[np.argmax(power)]
    epoch_phase = (epoch_no - (epoch_no //best_P) * best_P)/best_P
    epoch_phase = scale(epoch_phase)
    ominusc_phase = (ominusc - (ominusc //best_P) * best_P)/best_P
    ominusc_phase = scale(ominusc_phase)
    fap = ls.false_alarm_probability(power.max())
    
    levels = [0.5, 0.05, 0.01]
    false_alarm_levels = ls.false_alarm_level(levels)
    #print(frequency, power)
    pack = {'FAP':false_alarm_levels, 'Percentage':levels}
    period = 1/frequency[np.argmax(power)]
    # Fits
    fit_x = np.linspace(epoch_no.min(), epoch_no.max(), 1000)
    fit_y = ls.model(fit_x, frequency[np.argmax(power)])
    
    fit_x_phase = (fit_x - (fit_x //best_P) * best_P)/best_P
    fit_x_phase = scale(fit_x_phase)
    # Make figure and axes
    fig = plt.figure(figsize=(12,8))
    gs = gridspec.GridSpec(3, 1)
    plt.set_cmap('plasma')
    
    oc_ax = fig.add_subplot(gs[0])
    phase_ax = fig.add_subplot(gs[1])
    ls_ax = fig.add_subplot(gs[2])
    #t = np.arange(len(epoch_no))
    #Plot data
    oc_ax.errorbar(epoch_no, ominusc, ominuscerr, marker='.', 
                   elinewidth=0.8, color='dimgrey', linestyle='', 
                   capsize=2, alpha=0.8, zorder=1)
    oc_ax.scatter(epoch_no, ominusc, marker='.', zorder=2, c=epoch_no)
    oc_ax.axhline(0, color='black', linestyle='--', linewidth=1)
    oc_ax.plot(fit_x, fit_y, color='red', alpha=0.8)
    
    phase_ax.errorbar(epoch_phase, ominusc, ominuscerr, marker='.',
                      elinewidth=0.8, color='dimgrey', linestyle='', capsize=2,
                      alpha=0.8, zorder=1)
    phase_ax.scatter(epoch_phase, ominusc, c=epoch_no,
                     marker='.',  zorder=2, alpha=0.5)
    phase_ax.axhline(0, color='black', linestyle='--', linewidth=1)
    phase_ax.plot(fit_x_phase[np.argsort(fit_x_phase)], 
               fit_y[np.argsort(fit_x_phase)], color='red', alpha=0.8)
    
    #ls_ax.scatter(1/frequency, power, color='dimgrey', alpha=0.1, zorder=1, s=10)
    ls_ax.plot(1/frequency, power, linestyle='-', linewidth=0.75, zorder=2,
               marker='', color='k')
    
    pos = len(epoch_no)*0.985
    for (level, i) in zip(false_alarm_levels, levels):
        ls_ax.axhline(level, color='r', linestyle='--', alpha=0.8)
        ls_ax.annotate(f'{str(int(i*100))}'+'$\%$',
                       (pos, level*1.018), color='k', ha='center')
    if fap > 0.5:
        pass
    else:
        ls_ax.annotate(f'Period: {int(period)}\nFAP: {fap*100:.2f}$\%$',
                        (period*1.03, power.max()*1.03), color='k', weight='bold', ha='center')
    # Sort out labels etc
    oc_ax.set_xlabel('Epoch')
    oc_ax.set_ylabel('O-C (minutes)')
    phase_ax.set_xlabel('Epoch Phase')
    phase_ax.set_ylabel('O-C (minutes)')

    ls_ax.set_xlabel('Period (Epochs)')
    ls_ax.set_ylabel('Power')

    oc_ax.tick_params('both', which='both', direction='in', bottom=True, left=True)
    ls_ax.tick_params('both', which='both', direction='in', bottom=True, left=True)
    ls_ax.set_xlim([0, len(epoch_no)])
    ls_ax.set_ylim([0, power.max()*1.2])
    ls_ax.set_xscale('linear')

    fig.tight_layout()
    if exoplanet==None:
        fig.savefig('O-C_fold.jpg', bbox_inches='tight')
    else:
        fig.savefig(f'firefly/{exoplanet}/O-C_fold.jpg', bbox_inches='tight')
