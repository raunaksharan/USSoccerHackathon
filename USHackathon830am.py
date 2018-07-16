
# coding: utf-8

# In[3]:


# coding: utf-8

# In[39]:


import pandas as pd
import matplotlib.pyplot as plt


# filepath = '/Users/andrewmcwhirter/Desktop/Sample Data - Hackathon First 3 Matches.csv'

# sample_df = pd.read_csv(filepath, low_memory = False, header=0)

# list(sample_df)

def getKeeperID(inputDataFrame):
    keeper_set = set()
    lineups = inputDataFrame['involved'].dropna()
    for list in lineups:
        if list.count(",") > 3:
            keeper_set.add(list.split(',')[0])
    keeper_list = []
    for keep in keeper_set:
        keeper_list.append(keep)
    return keeper_list


# outcome 0=not successful, 1 = successful
event_type = 'Pass'


def getKeeperEvents(inputDataFrame, keeperList):
    trimmed_dataFrame = inputDataFrame[
        ['player_id', 'event_type', 'outcome', 'period_min', 'period_second', 'team', 'x', 'pass_end_x', 'game_id']]
    trimmed_dataFrame = trimmed_dataFrame.fillna(0)
    keeperEvents = pd.DataFrame(
        columns=['player_id', 'event_type', 'outcome', 'period_min', 'period_second', 'team', 'x', 'pass_end_x',
                 'game_id'])
    successDict = {}
    keeper_period_dict = {}
    for keeper in keeperList:
        success = 0
        attempt = 0
        flkeep = float(keeper)
        # print('Keeper:',keeper)
        keeper_period_list = []
        for row in trimmed_dataFrame.iterrows():
            if (row[1]['player_id'] == flkeep and row[1]['event_type'] == 'Pass'):
                keeper_period_list.append(
                    [row[1]['period_min'], row[1]['period_second'], row[1]['game_id'], row[1]['outcome']])
                keeperEvents = keeperEvents.append(row[1])
                attempt += 1
                if row[1]['outcome'] == 1:
                    success += 1
        # print(row[1]['player_id'])
        if attempt > 0:
            successRate = float(success) / float(attempt)
        else:
            successRate = 0.5
        successDict[keeper] = [successRate, success, attempt]
        keeper_period_dict[keeper] = keeper_period_list
    return keeperEvents, successDict, keeper_period_dict


def countPass(in_min, in_sec, inputDataFrame, game_id):
    posFlag = 0
    CheckNextFlag = 0
    total_pass = 0
    pos_pass = 0
    posTeam = None
    startSeconds = in_min * 60 + in_sec
    max_time = startSeconds + 20
    for row in inputDataFrame.iterrows():
        row_time = row[1]['period_min'] * 60 + row[1]['period_second']
        if ((row_time <= max_time) and (row_time >= (in_min * 60 + in_sec)) and row[1]['event_type'] == 'Pass' and
                row[1]['game_id'] == game_id):
            total_pass += 1
            if posTeam is None:
                posTeam = row[1]['team']
            if (row[1]['team'] == posTeam and row[1]['event_type'] == 'Pass'):
                pos_pass += 1
    return total_pass, pos_pass


def passAnalyticsAvgx(df1, minstart, minend, secstart, secend):
    df1['p'] = ((df1.period_min * 60 + df1.period_second) > (minstart * 60 + secstart)) & (
                (df1.period_min * 60 + df1.period_second) < (minend * 60 + secend)) & (df1.event_type == 'Pass')
    df1 = df1[df1['p']]
    # xavg=df1['x'].mean()
    xavgbyteam = df1.groupby('team')['x'].mean()
    try:
        keeper_team_avgx = xavgbyteam[0]
    except IndexError:
        keeper_team_avgx = 1000
    try:
        opponent_avgx = xavgbyteam[1]
    except IndexError:
        opponent_avgx = 0
    return keeper_team_avgx, opponent_avgx


def combineDicts(avgXDict, avgOpXDict, posDict, successPerDict):
    overallDict = {}
    for key in avgXDict.keys():
        keeperList = []
        keeperList.append(avgXDict[key])
        keeperList.append(100 - avgOpXDict[key])
        keeperList.append(posDict[key])
        keeperList.append(successPerDict[key])
        overallDict[key] = keeperList
    return overallDict


def hotMessOfCode(inputDataFrame, keeperList):
    df_keeper_events, df_keeper_success_dict, df_keeper_period_dict = getKeeperEvents(inputDataFrame, keeperList)
    df_keeper_x_dict = {}
    df_keeper_opx_dict = {}
    df_keeper_passPos_dict = {}
    one_game_list_of_lists = []
    new_keeper_success_dict = {}
    for key, value in df_keeper_period_dict.items():
        keeper_team_total = 0
        opponent_total = 0
        count = 0
        total_pass = 0
        total_pos = 0
        completed = 0
        for eventTime in value:
            completed += eventTime[3]
            if eventTime[1] > 39:
                endSec = eventTime[1] - 40
                endMin = eventTime[0] + 1
            else:
                endSec = eventTime[1] + 20
                endMin = eventTime[0]
            keeper_team_avg, opponent_avg = passAnalyticsAvgx(inputDataFrame, eventTime[0], endMin, eventTime[1],
                                                              endSec)
            if keeper_team_avg != 1000:
                keeper_team_total += keeper_team_avg
                opponent_total += opponent_avg
                count += 1
                tmp_total, tmp_pos = countPass(eventTime[0], eventTime[1], inputDataFrame, eventTime[2])
                total_pass += tmp_total
                total_pos += tmp_pos
            # pop
            if eventTime[2] == 958083 and key == 60582:
                game_list = []
                game_list.append('Success: ' + str(eventTime[3]))
                if tmp_total > 0:
                    game_list.append('Percent Pos: ' + str(tmp_pos / tmp_total))
                game_list.append('Team Average: ' + str(keeper_team_avg))
                game_list.append('Oppenent Average: ' + str(100 - opponent_avg))
                one_game_list_of_lists.append(game_list)
            # pop
        #if count > 0:
        keeper_succes = completed / count
        new_keeper_success_dict[key] = keeper_succes
    if total_pass > 0:
        team_pass_perc = total_pos / total_pass
    else:
        team_pass_perc = 0.5
    df_keeper_passPos_dict[key] = team_pass_perc
    if count > 0:
        keeper_final_avgX = keeper_team_total / count
        opponent_final_avgX = opponent_total / count
    else:
        keeper_final_avgX = 0.5
        opponent_final_avgX = 0.5
    df_keeper_x_dict[key] = keeper_final_avgX
    df_keeper_opx_dict[key] = opponent_final_avgX


    df_all_stats = combineDicts(df_keeper_x_dict, df_keeper_opx_dict, df_keeper_passPos_dict, new_keeper_success_dict)
    return df_all_stats


def getGameIDs(keeperId, inputDataFrame):
    game_set = set()
    inputDataFrame['p'] = inputDataFrame.player_id == keeperId
    for game in inputDataFrame[inputDataFrame['p']]['game_id']:
        game_set.add(game)
    return game_set



if __name__ == "__main__":
    fileloc = 'WorldCup.csv'
    main_df = pd.read_csv(fileloc, low_memory=False, header=0)
    main_df = main_df[
        ['player_id', 'event_type', 'outcome', 'period_min', 'period_second', 'team', 'x', 'pass_end_x', 'game_id']]
    keeperList = [[60772]]

    
    '''
    mls_fileloc = 'MLS2017-2018.csv'
    mls_df = pd.read_csv(mls_fileloc, low_memory=False, header=0,nrows=1000)
    mls_df=mls_df[['player_id','event_type','outcome','period_min','period_second','team','x','pass_end_x','game_id']]
    mls_keepers = [41210,202361,86938,78013,41705,157489,95309,94305,94932,224068,15310,221400,163906,164484,163484,109275,72775,110620,95298,60238,52629,95611,77521,15337]
    '''
    actualCombinedDict = {}
    rev = 1
    for sub_list in keeperList:
        game_list = []
        print('working on sublist #' + str(rev))
        rev += 1
        print('getting game list')
        for keeper in sub_list:
            game_set = getGameIDs(keeper, main_df)
            for game in game_set:
                game_list.append(game)
        print('Getting DF Subset')
        tmp_list = []
        print(game_list)
        print(main_df.game_id)
        for game_id in main_df.game_id:
            append_val = False
            for i in range(len(game_list)):
                if game_id == game_list[i]:
                    append_val = True
            tmp_list.append(append_val)
        #main_df['t'] = any(x in main_df.game_id for x in game_list)
        main_df['t'] = tmp_list
        print(main_df['t'].any)
        main_df_sub = main_df[main_df['t']]
        print('running the mass of code')
        tmp_combined = hotMessOfCode(main_df_sub, sub_list)
        print('HMC:' + str(tmp_combined))
        for key, value in tmp_combined.items():
            actualCombinedDict[key] = value
    print(actualCombinedDict)
    '''
    wc_keeper_events, wc_keeper_success_dict, wc_keeper_period_dict = getKeeperEvents(world_cup_df,world_cup_keepers)
    mls_keeper_events, mls_keeper_success_dict, mls_keeper_period_dict = getKeeperEvents(mls_df,mls_keepers)
    
    wc_keeper_x_dict = {}
    wc_keeper_opx_dict = {}
    wc_keeper_passPos_dict = {}
    one_game_list_of_lists = []
    new_keeper_success_dict = {}
    for key, value in wc_keeper_period_dict.items():
        keeper_team_total = 0
        opponent_total = 0
        count = 0
        total_pass = 0
        total_pos = 0
        completed = 0
        for eventTime in value:
            completed += eventTime[3]
            if eventTime[1] > 39:
                endSec = eventTime[1] - 40
                endMin = eventTime[0] + 1
            else:
                endSec = eventTime[1] + 20
                endMin = eventTime[0]
            keeper_team_avg, opponent_avg = passAnalyticsAvgx(world_cup_df, eventTime[0], endMin, eventTime[1], endSec)
            if keeper_team_avg != 1000:
                keeper_team_total += keeper_team_avg
                opponent_total += opponent_avg
                count += 1
                tmp_total, tmp_pos = countPass(eventTime[0], eventTime[1], world_cup_df, eventTime[2])
                total_pass += tmp_total
                total_pos += tmp_pos


        #pop
                if eventTime[2] == 958083 and key == 60582:
                    game_list = []
                    game_list.append('Success: ' + str(eventTime[3]))
                    if tmp_total>0:
                        game_list.append('Percent Pos: ' + str(tmp_pos/tmp_total))
                    game_list.append('Team Average: ' + str(keeper_team_avg))
                    game_list.append('Oppenent Average: ' + str(100-opponent_avg))
                    one_game_list_of_lists.append(game_list)
        #pop
            if count>0:
                keeper_succes = completed/count
                new_keeper_success_dict[key] = keeper_succes
            if total_pass > 0 :
                team_pass_perc = total_pos/total_pass
            else :
                team_pass_perc = 0.5
            wc_keeper_passPos_dict[key] = team_pass_perc
            if count > 0 :
                keeper_final_avgX = keeper_team_total/count
                opponent_final_avgX = opponent_total/count
            else :
                keeper_final_avgX = 0.5
                opponent_final_avgX = 0.5

            wc_keeper_x_dict[key] = keeper_final_avgX
            wc_keeper_opx_dict[key] = opponent_final_avgX

    wc_all_stats = combineDicts(wc_keeper_x_dict, wc_keeper_opx_dict, wc_keeper_passPos_dict, new_keeper_success_dict)


    mls_keeper_x_dict = {}
    mls_keeper_opx_dict = {}
    mls_keeper_passPos_dict = {}
    for key,value in mls_keeper_period_dict.items():
        keeper_team_total = 0
        opponent_total = 0
        count = 0
        total_pass = 0
        total_pos = 0
        for eventTime in value:
            if eventTime[1] > 39:
                endSec = eventTime[1] - 40
                endMin = eventTime[0] + 1
            else :
                endSec = eventTime[1] + 20
                endMin = eventTime[0]
            keeper_team_avg,opponent_avg = passAnalyticsAvgx(mls_df,eventTime[0],endMin, eventTime[1],endSec)
            keeper_team_total += keeper_team_avg
            opponent_total += opponent_avg
            count += 1
            tmp_total, tmp_pos = countPass(eventTime[0], eventTime[1], mls_df, eventTime[2])
            total_pass += tmp_total
            total_pos += tmp_pos
        if total_pass > 0 :
            team_pass_perc = total_pos/total_pass
        else :
            team_pass_perc = 0.5
        mls_keeper_passPos_dict[key] = team_pass_perc
        if count > 0 :
            keeper_final_avgX = keeper_team_total/count
            opponent_final_avgX = opponent_total/count
        else :
            keeper_final_avgX = 0.5
            opponent_final_avgX = 0.5

        mls_keeper_x_dict[key] = keeper_final_avgX
        mls_keeper_opx_dict[key] = opponent_final_avgX

    mls_all_stats = combineDicts(mls_keeper_x_dict,mls_keeper_opx_dict,mls_keeper_passPos_dict,mls_keeper_success_dict)
    #return wc_all_stats,mls_all_stat
    print(wc_all_stats)
    print(one_game_list_of_lists)
    for key , value in mls_all_stats.items():
        finaldf=pd.DataFrame.from_dict(mls_all_stats)
    pd.DataFrame.to_csv(finaldf)
    '''

