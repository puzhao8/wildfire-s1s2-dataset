
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.dates as mdates
from datetime import datetime
from matplotlib import rcParams
from pathlib import Path
import os
rcParams['font.family'] = 'sans-serif'

def plot_timeline(msiDateList=[], sarDateList=[], FIGURE_TITLE='wildfire', 
                BOTTOM=0.1, SENSOR_FLAG=True, ORBIT_FLAG=True, YOUR_DATE_FORMAT = "%Y%m%dT%H:%M"):

    

    # In case the above fails, e.g. because of missing internet connection
    # use the following lists as fallback.

    dates = sorted(msiDateList)
    names = dates

    dateSAR = sorted(sarDateList)
    nameSAR = dateSAR


    # Convert date strings (e.g. 2014-10-18) to datetime
    dates = [datetime.strptime(d.split('_')[0], YOUR_DATE_FORMAT) for d in dates]

    # Choose some nice levels
    levels = np.tile([1, 1.5, 3, 3.5, 2, 0.5],
                    int(np.ceil(len(dates)/6)))[:len(dates)]

    dates_sar = [datetime.strptime(d.split('_')[0], YOUR_DATE_FORMAT) for d in dateSAR]

    # Choose some nice levels
    levels_sar = np.tile([-2, -3, -3.5, -2.5, -1, -0.5],
                    int(np.ceil(len(dates_sar) / 6)))[:len(dates_sar)]

    """ Create figure and plot a stem plot with the date """
    fig, ax = plt.subplots(figsize=(8.8, 4), constrained_layout=False) #8.8, 4
    # ax.set(title=FIGURE_TITLE)

    """ ========================> For MS Dates <======================== """
    markerline, stemline, baseline = ax.stem(dates, levels,
                                            linefmt="g-", basefmt="g-",
                                            use_line_collection=True,
                                            label='S2/L8: MS',
                                            bottom=BOTTOM)

    plt.setp(markerline, mec="k", mfc="w", zorder=3)

    # Shift the markers to the baseline by replacing the y-data by zeros.
    markerline.set_ydata(BOTTOM+np.zeros(len(dates)))


    if SENSOR_FLAG:
        """ annotate lines if you want add sensor name """
        vert = np.array(['top', 'bottom'])[(levels > 0).astype(int)]
        for d, l, r, va, sensor in zip(dates, levels, names, vert, msiDateList):
            sensorName = sensor.split('_')[-1]
            ax.annotate(r.split('T')[0][-4:]+'-'+sensorName, xy=(d, l), xytext=(15, np.sign(l)*3),
                        textcoords="offset points", va=va, ha="right")
    else:
        """ annotate lines """
        vert = np.array(['top', 'bottom'])[(levels > 0).astype(int)]
        for d, l, r, va in zip(dates, levels, names, vert):
            ax.annotate(r.split('T')[0][-4:], xy=(d, l), xytext=(15, np.sign(l)*3),
                        textcoords="offset points", va=va, ha="right")



    """ =======================> For SAR Dates <========================= """
    markerline, stemline, baseline = ax.stem(dates_sar, levels_sar,
                                            linefmt="C1-", basefmt="C1-",
                                            use_line_collection=True,
                                            label='S1: C-SAR',
                                            bottom=BOTTOM*(-1))

    plt.setp(markerline, mec="k", mfc="w", zorder=3)

    # Shift the markers to the baseline by replacing the y-data by zeros.
    markerline.set_ydata(BOTTOM*(-1)+np.zeros(len(dates_sar)))

    """ annotate lines """
    if ORBIT_FLAG:
        vert = np.array(['top', 'bottom'])[(levels_sar > 0).astype(int)]
        for d, l, r, va, imgLabel in zip(dates_sar, levels_sar, nameSAR, vert, sarDateList):
            orbit = imgLabel.split("_")[-1].replace('SC','')
            ax.annotate(r.split('T')[0][-4:]+'-'+orbit, xy=(d, l), xytext=(15, np.sign(l)*3),
                        textcoords="offset points", va=va, ha="right")
    else:
        vert = np.array(['top', 'bottom'])[(levels_sar > 0).astype(int)]
        for d, l, r, va in zip(dates_sar, levels_sar, nameSAR, vert):
            ax.annotate(r.split('T')[0][-4:], xy=(d, l), xytext=(15, np.sign(l)*3),
                        textcoords="offset points", va=va, ha="right")

    # format xaxis with 4 month intervals
    ax.get_xaxis().set_major_locator(mdates.DayLocator(interval=7))
    ax.get_xaxis().set_major_formatter(mdates.DateFormatter("%d %b %Y"))
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")

    # remove y axis and spines
    ax.get_yaxis().set_visible(False)
    for spine in ["left", "top", "right"]:
        ax.spines[spine].set_visible(False)

    """ Plot and Save """
    ax.margins(y=0.1)
    # plt.legend(loc=0, bbox_to_anchor=(-0.12, 0.5, 0.5, 0.5))
    plt.tight_layout()

    # savePath = Path(f"{os.getcwd()}/outputs")
    # if not os.path.exists(savePath): os.mkdir(savePath)
    # print(str(savePath / f'{FIGURE_TITLE}_timeline.pdf'))
    # plt.savefig(savePath / f'{FIGURE_TITLE}_timeline.pdf')
    # plt.savefig(savePath / f'{FIGURE_TITLE}_timeline.png', dpi=300)
    # plt.show()
    return fig, ax


if __name__ == "__main__":

    msiDateList = [
        '20191022T00:05_S2',
        '20191027T00:05_S2',
        '20191028T23:49_L8',
        '20191101T00:05_S2',
        '20191106T00:05_S2',
        '20191111T00:05_S2',
        '20191113T23:49_L8',
        '20191121T00:05_S2',
        '20191211T00:05_S2',
        '20191216T00:05_S2',
        '20191221T00:05_S2',
        '20191226T00:05_S2',
        '20191231T00:05_S2',
        '20191231T23:49_L8',
        '20200105T00:05_S2',
        '20200110T00:05_S2'
                ]


    sarDateList = [
        '20191028T08:38_ASC9',
        '20191106T19:15_DSC147',
        '20191109T08:38_ASC9',
        '20191118T19:15_DSC147',
        '20191121T08:38_ASC9',
        '20191127T08:38_ASC9',
        '20191130T19:15_DSC147',
        '20191212T19:15_DSC147',
        '20191215T08:38_ASC9',
        '20191224T19:15_DSC147',
        '20191227T08:38_ASC9',
        '20200105T19:15_DSC147',
        '20200108T08:38_ASC9'
    ]

    """ Set Global Variable """
    YOUR_DATE_FORMAT = "%Y%m%dT%H:%M"
    FIGURE_TITLE = "Wildfire Near Sydney, Australia (Oct. 2019-Jan., 2020)"
    BOTTOM = 0.1 # used to control baseline
    SAVENAME = 'Sydney_V2'

    SENSOR_FLAG = True
    ORBIT_FLAG = True
    fig, ax = plot_timeline(msiDateList, sarDateList)
    plt.savefig('timeline.png')
    plt.show()
    