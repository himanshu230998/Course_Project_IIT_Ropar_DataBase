import psycopg2
from flask import Flask, render_template, redirect, url_for, request,flash
import datetime
import bcrypt
import datetime
import bson
import time
import mongoengine
from typing import List, Optional

path = 'hod->deanfa->dir'
active_account = None

app = Flask(__name__)
app.secret_key = "super secret key"

gsk = {
    'hod':'hod',
    'deanfa': 'Dean Faculty Affairs',
    'dir': 'Director'
}

try:
    conn = psycopg2.connect(database = "project", user = "postgres", password = "Himanshu1$", host = "127.0.0.1", port = "5432")
    print("Opened database successfully")
except:
    print("Error Opening Database")
    exit(0)


def connectgs():
    return psycopg2.connect(database = "project", user = "postgres", password = "Himanshu1$", host = "127.0.0.1", port = "5432")

def get_next_member_id(reqid,pth):
    global active_account

    con = connectgs()
    cur = con.cursor()
    cur1 = con.cursor()
    cur2 = con.cursor()
    cur.execute('select * from crossFaculty where facultyId = \'{}\''.format(reqid))
    cur1.execute('select * from HOD where facultyId = \'{}\''.format(reqid))
    nextmem = "&"
    pos = "&"
    path = pth.split('$')
    # if deanfa is present and they are requesting leave to dir
    if(cur.rowcount==1):
        num = cur.fetchone()
        position = num[1]
        for i in range(len(path)):
            if(path[i]==position):
                if(i!=len(path)-1):
                    pos = path[i+1]
                    cur.execute('select facultyId from crossFaculty where position = \'{}\''.format(pos))
                    if(cur.rowcount==0):
                        nextmem = "7"
                    else :
                        nextmem = cur.fetchone()
                        cur.execute('select positionid from leaves where positionid = \'{}\''.format(reqid))
                        if(nextmem[0] != reqid):
                            cur2.execute("update leaves set positionid = \'{}\' where facultyId = \'{}\'".format(reqid, active_account))
                else :
                    pos = "&"
                    nextmem = ("$")
                break
        cur.close()
        cur2.close()
    # if hod is present and they are requesting leave to dir
    elif(cur1.rowcount==1):

        position = 'HOD'
        position1 = 'hod'
        for i in range(len(path)):
            if(path[i]==position or path[i] == position1):
                if(i!=len(path)-1):
                    pos = path[i+1]
                    cur1.execute('select facultyId from crossFaculty where position = \'{}\''.format(pos))
                    if(cur1.rowcount==0):
                        nextmem = "7"
                    else :
                        nextmem = cur1.fetchone()
                        if(nextmem[0]!=reqid):
                            cur2.execute("update leaves set positionid = \'{}\' where facultyId = \'{}\'".format(reqid, active_account))
                else :
                    pos=""
                    nextmem = ("$")
                break
        cur1.close()
        cur2.close()
    # if faculty are requesting leave
    else :
        pos = path[0]
        if(pos=='HOD' or pos =='hod'):
            cur = con.cursor()
            cur.execute('select department from faculty where id = \'{}\''.format(reqid))
            dept = cur.fetchone()
            cur.execute('select facultyId from HOD where departname = \'{}\''.format(dept[0]))
            if(cur.rowcount==0):
                nextmem = "7"
            else :
                nextmem = cur.fetchone()
                if(active_account!=reqid):
                    cur2.execute("update leaves set positionid = \'{}\' where facultyId = \'{}\'".format(reqid, active_account))
                    print(nextmem[0],reqid, active_account)
            cur.close()
        else:
            cur = con.cursor()
            cur.execute('select facultyId from crossFaculty where position = \'{}\''.format(pos))
            if(cur.rowcount==0):
                nextmem = "7"
            else :
                nextmem = cur.fetchone()
            cur.close()
    con.close()
    cur2.close()
    return (pos,nextmem[0])

# def get_leaves(rows):
#     leaves = []
#     for i in rows:
#         gs = list(i)
#         leaves.append(gs)
#     return leaves

def my_leave_application_status(fid):
    con = connectgs()
    cur = con.cursor()
    cur.execute('select * from leaves where facultyId = \'{}\' order by (lastupdated) desc'.format(fid))
    leaves = cur.fetchall()
    # leaves = get_leaves(rows)
    cur.close()
    con.close()
    return leaves


def recieved_leave_applications(fid):
    con = connectgs()
    cur = con.cursor()
    cur.execute("select * from leaves where positionid = \'{}\' and facultyId != positionid order by (lastupdated) ".format(fid))
    leaves = cur.fetchall()
    cur.close()
    con.close()
    return leaves

@app.route('/comments',methods=['POST','GET'])
def showcomments():
    lid = ""
    lid = request.args.get('type')
    con = connectgs()
    cur = con.cursor()
    cur.execute('select * from comments where leaveid = {} order by (timeofcomment) desc'.format(lid))
    comm = cur.fetchall()
    cur.close()
    con.close()
    # comm = get_leaves(rows)
    return render_template('comments.html',posts=comm)

@app.route('/request',methods=['POST','GET'])
def request_for_leave():
    global path
    global active_account
    requestor_id = ""
    no_of_days = 0
    comment = ""
    if request.method == 'POST':
        if('retrospective_leave' in request.form['option']):
            if(active_account != None):
                info_dict = {'name':find_account_by_email(active_account)[2], 'email':find_account_by_email(active_account)[0], 'department':find_account_by_email(active_account)[1]}
            requestor_id = request.form['id']
            no_of_days = request.form['nm']
            startdate = request.form['date']
            comment = request.form['cm']
            con = connectgs()
            cur = con.cursor()
            cur1 = con.cursor()
            cur2 = con.cursor()
            rpth=''
            cur.execute('select * from crossFaculty where facultyId = \'{}\''.format(requestor_id))
            cur1.execute('select * from hod where facultyId = \'{}\''.format(requestor_id))
            pth = path
            cur2.execute('select * from faculty where id = \'{}\''.format(requestor_id))
            faculty_row = cur2.fetchone()
            if(int(faculty_row[1]) - int(no_of_days) < 0):
                redirect(url_for('index'))
            requestingNextLeaves = faculty_row[1] - int(no_of_days)
            if(requestingNextLeaves > 0):
                requestingNextLeaves = 0
            else:
                requestingNextLeaves = abs(requestingNextLeaves)
            # if dean are requesting
            if(cur.rowcount==1):
                rpth = 'deanfa$dir'
                pos = 'dir'
                cur1.execute("select * from crossFaculty where position = 'dir'")
                nextid = cur1.fetchone()[0]
            # if hod are requesting
            elif(cur1.rowcount==1):
                rpth = 'hod$dir'
                pos = 'dir'
                cur1.execute("select * from crossFaculty where position = 'dir'")
                nextid = cur1.fetchone()[0]

            else :
                path1 = 'hod->deanfa->dir'
                path1 = path1.split('->')
                for s in range(len(path1)):
                    if(s != len(path1)-1):
                        rpth = rpth + path1[s] + '$'
                    else :
                        rpth = rpth + path1[s]
                pos,nextid = get_next_member_id(requestor_id,rpth)
           
            if(nextid=="7"):
                redirect(url_for('index'))
            if(nextid=="$"):
                redirect(url_for('index'))
            con = connectgs()
            cur = con.cursor()
            cur.execute('select * from leaves where facultyid = \'{}\' and (leavestatus = \'requested\' or leavestatus = \'redirected\')'.format(requestor_id))
            if(cur.rowcount==0):
                cur.execute('insert into leaves values(DEFAULT,\'requested\',\'{}\',\'{}\',\'{}\',\'{}\',now(),\'{}\', \'{}\',\'{}\')'.format(requestor_id,pos,nextid,no_of_days,rpth, "Retrospective leave",datetime.datetime.strptime(startdate, '%Y-%m-%d')))
                cur.execute("select * from leaves where leavestatus='requested' and facultyid = '{}' and positionid = '{}' ".format(requestor_id,nextid))
                #add code to include comment
                rvn = cur.fetchone()
                create_comment(rvn[0],requestor_id,'faculty',comment)
                cur.close()
                con.commit()
                con.close()
                return render_template('info.html', info_dict = info_dict, status3='Leave requested successfully')
            else:
                cur.close()
                con.commit()
                con.close()
                return render_template('info.html', info_dict = info_dict, status3='one leave request is already in pending')

            return redirect(url_for('index'))
        else:
            requestor_id = request.form['id']
            no_of_days = request.form['nm']
            startdate = request.form['date']
            comment = request.form['cm']
            con = connectgs()
            cur = con.cursor()
            cur1 = con.cursor()
            cur2 = con.cursor()
            rpth=''
            cur.execute('select * from crossFaculty where facultyId = \'{}\''.format(requestor_id))
            cur1.execute('select * from hod where facultyId = \'{}\''.format(requestor_id))
            pth = path
            cur2.execute('select * from faculty where id = \'{}\''.format(requestor_id))
            faculty_row = cur2.fetchone()
            if(int(faculty_row[1]) - int(no_of_days) < 0):
                flash('Number of leaves requested are more than available which are this year -> {}, next year {}'.format(faculty_row[1], faculty_row[3]),'error')
                return redirect(url_for('index'))
            requestingNextLeaves = faculty_row[1] - int(no_of_days)
            if(requestingNextLeaves > 0):
                requestingNextLeaves = 0
            else:
                requestingNextLeaves = abs(requestingNextLeaves)
            # if dean are requesting
            if(cur.rowcount==1):
                rpth = 'deanfa$dir'
                pos = 'dir'
                cur1.execute("select * from crossFaculty where position = 'dir'")
                nextid = cur1.fetchone()[0]
            # if hod are requesting
            elif(cur1.rowcount==1):
                rpth = 'hod$dir'
                pos = 'dir'
                cur1.execute("select * from crossFaculty where position = 'dir'")
                nextid = cur1.fetchone()[0]

            else :
                path1 = 'hod->deanfa'
                path1 = path1.split('->')
                for s in range(len(path1)):
                    if(s != len(path1)-1):
                        rpth = rpth + path1[s] + '$'
                    else :
                        rpth = rpth + path1[s]
                pos,nextid = get_next_member_id(requestor_id,rpth)
           
            if(nextid=="7"):
                flash('can not create leave application may be next member in path doesnot exist','error')
                return redirect(url_for('index'))
            if(nextid=="$"):
                flash('last member in path can not apply for leave','error')
                return redirect(url_for('index'))
            con = connectgs()
            cur = con.cursor()
            cur.execute('select * from leaves where facultyid = \'{}\' and (leavestatus = \'requested\' or leavestatus = \'redirected\')'.format(requestor_id))
            if(cur.rowcount==0):
                cur.execute('insert into leaves values(DEFAULT,\'requested\',\'{}\',\'{}\',\'{}\',\'{}\',now(),\'{}\', \'{}\',\'{}\')'.format(requestor_id,pos,nextid,no_of_days,rpth,"Simple leave" ,datetime.datetime.strptime(startdate, '%Y-%m-%d')))
                flash('leave requested successfully','success')
                cur.execute("select * from leaves where leavestatus='requested' and facultyid = '{}' and positionid = '{}' ".format(requestor_id,nextid))
                #add code to include comment
                rvn = cur.fetchone()
                create_comment(rvn[0],requestor_id,'faculty',comment)
            else :
                flash('one leave request is already in pending','success')
            cur.close()
            con.commit()
            con.close()
            return redirect(url_for('index'))
        return redirect(url_for('index'))
    
@app.route("/leavelist",methods=['POST','GET'])
def my_leaves():
    s=""
    if request.method == 'POST':
        s = request.form['id']
    leave = my_leave_application_status(s)
    return render_template('viewmylist.html',posts=leave)

@app.route("/accept",methods=['POST','GET'])
def accept():
    lid = 0
    comment = ""
    if request.method == 'POST':
        lid = int(request.form['id'])
        comment = request.form['cm']
    con = connectgs()
    cur = con.cursor()
    cur.execute('select * from leaves where id = {}'.format(lid))
    row = cur.fetchone()
    cur.execute("select * from faculty where Id = '{}'".format(row[2]))
    note = 0
    row2 = cur.fetchone()
    l = row2[1] - row[5]
    x = row2[3]
    if(l < 0):
        note = abs(l)
        x = row2[3] + l
        l = 0
    
    cur.execute('update leaves set leavestatus = \'accepted\',positionid = \'{}\',lastupdated=now() where id = {}'.format(row[2], lid))
    cur.execute("update faculty set noOfLeaves = '{}', next_year_leaves = '{}' where Id = '{}'".format(l, x, row[2]))
    cur.close()
    con.commit()
    con.close()
    create_comment(lid,row[4],row[3],comment)
    return redirect(url_for('req_leaves'))

@app.route("/reject",methods=['POST','GET'])
def reject():
    lid = 0
    comment = ""
    if request.method == 'POST':
        lid = int(request.form['id'])
        comment = request.form['cm']
    con = connectgs()
    cur = con.cursor()
    cur.execute('select * from leaves where id = {}'.format(lid))
    row = cur.fetchone()
    cur.execute('update leaves set leavestatus = \'rejected\',positionid = \'{}\',lastupdated=now() where id = {}'.format(row[2],lid))
    
    cur.close()
    con.commit()
    con.close()
    create_comment(lid,row[4],row[3],comment)
    return redirect(url_for('req_leaves'))

@app.route("/reqleavelist",methods=['POST','GET'])
def req_leaves():
    s=""
    if request.method == 'POST':
        s = request.form['id']
    leave = recieved_leave_applications(s)
    return render_template('reqlistview.html',posts=leave)

@app.route("/forward",methods=['POST','GET'])
def forward():
    lid = 0
    comment = ""
    if request.method == 'POST':
        lid = int(request.form['id'])
        comment = request.form['cm']
    con = connectgs()
    cur = con.cursor()
    cur.execute('select * from leaves where id = {}'.format(lid))
    row = cur.fetchone()
    pos,nextmem = get_next_member_id(row[4],row[len(row)-3])

    cntr = 0
    if(nextmem[0]=='$' or nextmem =="$") :
        print('can not forward')
    elif (nextmem[0]=='7' or nextmem == '7') :
        print("path position and member position are not matching","error")
    else :
        cur.execute('update leaves set leavestatus = \'requested\',positionid = \'{}\',position=\'{}\',lastupdated=now() where id = {}'.format(nextmem,pos,lid))
        cntr=1
    cur.close()
    con.commit()
    con.close()

    if(row[1]=='redirected'):
        if(cntr==1):
            create_comment(lid,row[4],"faculty(me)",comment)

        return redirect(url_for('my_leaves'))
    else :
        if(cntr==1):
            create_comment(lid,row[4],row[3],comment)
        return redirect(url_for('req_leaves'))


def create_comment(lid,comenterid,pos,s):
    con = connectgs()
    cur = con.cursor()
    cur.execute('insert into comments values({},\'{}\',\'{}\',\'{}\')'.format(lid,s,comenterid,pos))
    cur.close()
    con.commit()
    con.close()


@app.route("/redirect",methods=['POST','GET'])
def redirect_to_sender():
    lid = 0
    comment = ""
    if request.method == 'POST':
        lid = int(request.form['id'])
        comment = request.form['cm']
    con = connectgs()
    cur = con.cursor()
    cur.execute('select * from leaves where id = {}'.format(lid))
    row = cur.fetchone()
    cur.execute('update leaves set leavestatus =\'redirected\',positionid = \'{}\',lastupdated = now() where id = {}'.format(row[2],lid))
    cur.close()
    con.commit()
    con.close()
    create_comment(lid,row[4],row[3],comment)
    #return redirect(url_for('leaves',s=row[4]))
    #leave = recieved_leave_applications(row[4])
    #return render_template('viewmylist.html',posts=leave)
    return redirect(url_for('req_leaves'))

###############################leave ends###########################################
    # conn = connectgs()
    # cur = conn.cursor()
    # cur.execute("select id from leaves where facultyid = {} and startdate<now() and leavestatus!=\'rejected'\.format(fid);")
    # for(len(x)):
    #   x = cur.fetchall()
    #   cur.execute('update leaves set leavestatus =\'rejected-system error\',lastupdated = now() where id = {}'.format(x[0],lid))
    # cur.close()
####





@app.route('/')
@app.route('/info', methods = ['GET', 'POST'])
def index():
    global path
    global active_account
    #admin
    if(active_account != None and active_account == 'admin@admin.com'):
       return render_template('admin.html', path = path)
    #users
    if(active_account != None):
        info_dict = {'name':find_account_by_email(active_account)[2], 'email':find_account_by_email(active_account)[0], 'department':find_account_by_email(active_account)[1]}
        info = getInfo(active_account)
        con = connectgs()
        cur = con.cursor()
        cur1 = con.cursor()
        cur.execute('select * from crossFaculty where facultyId = \'{}\''.format(active_account))
        cur1.execute('select * from hod where facultyId = \'{}\''.format(active_account))
        pos_crossfaculty = ''
        pos_hod = ''
        if(cur.rowcount==1):
            row = cur.fetchone()
            pos_crossfaculty = row[1]
        if(cur1.rowcount==1):
            pos_hod = 'hod'
        cur.close()
        cur1.close()
        con.close()

        # director
        if(len(pos_crossfaculty)!=0 and pos_crossfaculty == 'dir' and len(pos_hod)==0):
            if(request.method == 'POST'):
                if 'SetHOD' in request.form:
                    if request.form['CHOD'] is None:
                        return render_template('info.html',info = info , info_dict = info_dict, error1='Need Department', pos = gsk[pos_crossfaculty])
                    email = request.form['newHOD']
                    if (find_account_by_email(email)==0):
                        return render_template('info.html',info = info , info_dict = info_dict, error1='Faculty Not present', pos = gsk[pos_crossfaculty])
                    conn = connectgs()
                    cur = conn.cursor()
                    cur.execute("select position from crossfaculty where facultyid = \'%s\'" % (str(email)))
                    data = cur.fetchone()
                    if data is not None:
                        return render_template('info.html',info = info , info_dict = info_dict, error1='Faculty Already a Cross Faculty', pos = gsk[pos_crossfaculty])
                    dept = str(request.form['CHOD'])
                    eid = str(email)
                    if (find_account_by_email(email)[1] != dept):
                        return render_template('info.html',info = info , info_dict = info_dict, error1='Faculty Should be of same department', pos = gsk[pos_crossfaculty])
                    cur.execute("select changeHod(%s, %s)", (dept, email))
                    cur.close()
                    conn.commit()
                    conn.close()
                    ###change
                    conn = connectgs()
                    cur = conn.cursor()
                    cur.execute("select * from leaves")
                    x = cur.fetchall()

                    for i in range(len(x)):
                        print('SetHOD', email)
                        if((x[i][1]=='requested' or x[i][1]=='redirected') and x[i][3]=='hod' ):
                            cur.execute("update leaves set positionid = '{}' where Id = '{}'".format(email,x[i][0]))
                    cur.close()
                    conn.commit()
                    conn.close()
                    return render_template('info.html',info = info , info_dict = info_dict, status1='HOD updated Succesfully', pos = gsk[pos_crossfaculty])
                if 'SetDEAN' in request.form:
                    if request.form['CDEAN'] is None:
                        return render_template('info.html',info = info , info_dict = info_dict, error2='Need Department', pos = gsk[pos_crossfaculty])
                    email = request.form['newDEAN']
                    if (find_account_by_email(email)==0):
                        return render_template('info.html',info = info , info_dict = info_dict, error2='Faculty Not present', pos = gsk[pos_crossfaculty])
                    conn = connectgs()
                    cur = conn.cursor()
                    cur.execute("select position from crossfaculty where facultyid = \'%s\'" % (str(email)))
                    data = cur.fetchone()
                    if data is not None:
                        return render_template('info.html',info = info , info_dict = info_dict, error2='Faculty Already a Cross Faculty', pos = gsk[pos_crossfaculty])
                    
                    dept = str(request.form['CDEAN'])
                    email = str(email)
                    cur.execute("select changeCross(%s, %s)", (dept, email))
                    cur.close()
                    conn.commit()
                    conn.close()
                    ###change
                    conn = connectgs()
                    cur = conn.cursor()
                    cur.execute("select * from leaves")
                    x = cur.fetchall()

                    for i in range(len(x)):
                        print('SetDEAN', email)
                        if((x[i][1]=='requested' or x[i][1]=='redirected') and x[i][3]=='deanfa' ):
                            cur.execute("update leaves set positionid = '{}' where Id = '{}'".format(email,x[i][0]))
                    cur.close()
                    conn.commit()
                    conn.close()
                    return render_template('info.html',info = info , info_dict = info_dict, status2 = 'Dean updated successfully', pos = gsk[pos_crossfaculty])
                
            return render_template('info.html',info = info , info_dict = info_dict, pos = gsk[pos_crossfaculty])
        # dean
        elif(len(pos_crossfaculty)!=0 and pos_crossfaculty != 'dir' and len(pos_hod)==0):
            return render_template('info.html',info = info , info_dict = info_dict, pos = gsk[pos_crossfaculty])
        elif(len(pos_crossfaculty)==0 and len(pos_hod)!=0):
            return render_template('info.html',info = info , info_dict = info_dict, pos = gsk[pos_hod])
        else:
            return render_template('info.html',info = info , info_dict = info_dict)
    else:
        return render_template('login.html')




@app.route('/admin', methods = ['GET', 'POST'])
def admin():
    global path
    global active_account
    if(active_account == None or active_account != 'admin@admin.com'):
        return render_template('login.html')
    if(request.method == 'POST'):
        
        if 'SetDIR' in request.form:
            email = request.form['newDIR']
            if (find_account_by_email(email)==0):
                return render_template('admin.html', path = path,  error3='Faculty Not present')
            conn = connectgs()
            cur = conn.cursor()
            cur.execute("select position from crossfaculty where facultyid = \'%s\'" %(str(email)))
            data = cur.fetchone()
            if data is not None:
                return render_template('admin.html', path = path, error3='Faculty Already a Cross Faculty')
            
            email = str(email)
            cur.execute("select changeCross(%s, %s)", ('dir', str(email)))
            cur.close()
            conn.commit()
            conn.close()
            conn = connectgs()
            cur = conn.cursor()
            cur.execute("select * from leaves")
            x = cur.fetchall()

            for i in range(len(x)):
                print('SetDIR', email)
                if((x[i][1]=='requested' or x[i][1]=='redirected') and x[i][3]=='dir' ):
                    cur.execute("update leaves set positionid = '{}' where Id = '{}'".format(email,x[i][0]))
            cur.close()
            conn.commit()
            conn.close()
            return render_template('admin.html', path = path, status3='Director updated Succesfully')
    return render_template('admin.html', path = path )

@app.route('/login', methods=['GET', 'POST'])
def login():
    global active_account
    if(request.method == 'POST'):
        email = request.form['emailid']
        password = request.form['password'].encode('utf-8')
        if(email!='admin@admin.com'): 
            if(find_account_by_email(email)!=0):
                oemail, odepartment, oname, opassword =find_account_by_email(email)
                opassword = opassword.encode('utf-8')
                if bcrypt.hashpw(password, opassword) == opassword:
                    active_account = email
                    return redirect(url_for('index'))
            else:
                msg = 'Invalid Email or Password'
                return render_template('login.html', msg = msg)
        else:
            if(find_account_by_email(email)!=0):
                oemail, opassword=find_account_by_email(email)
                opassword = opassword.encode('utf-8')
                if bcrypt.hashpw(password, opassword) == opassword:
                    active_account = email
                    if(active_account == 'admin@admin.com'):
                        return redirect(url_for('admin'))
                    return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/viewProfile', methods=['GET', 'POST'])
def viewProfile():
    if(request.method == 'POST'):
        email = request.form['emailid']
        if(email!='admin@admin.com'): 
            if(find_account_by_email(email)!=0):
                info_dict = {'name':find_account_by_email(email)[2], 'email':find_account_by_email(email)[0], 'department':find_account_by_email(email)[1]}
                info = getInfo(email)
                con = connectgs()
                cur = con.cursor()
                cur1 = con.cursor()
                cur.execute('select * from crossFaculty where facultyId = \'{}\''.format(email))
                cur1.execute('select * from hod where facultyId = \'{}\''.format(email))
                pos = ''
                if(cur.rowcount==1):
                    row = cur.fetchone()
                    pos= row[1]
                if(cur1.rowcount==1):
                    pos = 'hod'
                cur.close()
                cur1.close()
                con.close()
                return render_template('facultyInfo.html', info_dict = info_dict, info = info, pos = pos)
            else:
                msg = 'No faculty with this email id '
                return render_template('login.html', msg = msg)
        else:
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/user/<facultyName>', methods=['GET', 'POST'])
def facultyName(facultyName):
    conn = connectgs()
    cur = conn.cursor()
    facultyName = facultyName[1:len(facultyName)-1]
    cur.execute("select id from faculty where name = '{}'".format(facultyName))
    email = cur.fetchone()
    print('facultyName', email[0])
    email = email[0]
    cur.close()
    conn.close()
    con = connectgs()
    cur = con.cursor()
    cur1 = con.cursor()
    cur.execute('select * from crossFaculty where facultyId = \'{}\''.format(email))
    cur1.execute('select * from hod where facultyId = \'{}\''.format(email))
    pos = ''
    if(cur.rowcount==1):
        row = cur.fetchone()
        pos = row[1]
    if(cur1.rowcount==1):
        pos = 'hod'
    cur.close()
    cur1.close()
    con.close()
    if(email!='admin@admin.com'): 
        if(find_account_by_email(email)!=0):
            info_dict = {'name':find_account_by_email(email)[2], 'email':find_account_by_email(email)[0], 'department':find_account_by_email(email)[1]}
            info = getInfo(email)
            return render_template('facultyInfo.html', info_dict = info_dict, info = info, pos = pos )
        else:
            msg = 'No faculty with this name '
            return render_template('login.html', msg = msg)
    else:
        return redirect(url_for('login.html'))        
        

@app.route('/logout')
def logout():
    global active_account
    active_account = None
    return redirect(url_for('login'))

@app.route('/register', methods = ['GET', 'POST'])
def register():
    global active_account
    if(request.method == 'POST'):
        name = request.form['username']
        email = request.form['emailid']
        password = request.form['password'].encode('utf-8')
        department = request.form['department']
        if(email!='admin@admin.com'):
            if not name or not email or not password or not department :
                msg = 'Fill all the info'
                return render_template('register.html', msg = msg)
            
            hashed = bcrypt.hashpw(request.form['password'].encode('utf-8'), bcrypt.gensalt())
            if(find_account_by_email(email)):
                oemail, odepartment, oname, opassword=find_account_by_email(email)
                old_account=oemail
                if (old_account==email):
                    msg = 'Account of same email already exists'
                    return render_template('register.html', msg = msg)
            
            create_account_by_flask(name, email, department, hashed.decode('utf-8'))
            active_account = email
            return redirect(url_for('index'))
        else:
            msg = 'Admin needs to login with password without registration'
            return render_template('login.html', msg = msg)
        
    return render_template('register.html')

@app.route('/edit', methods = ['GET', 'POST'])

def edit():
    #active_account_mongo=create_account_by_flask_mongo(find_account_by_email(active_account)[2], find_account_by_email(active_account)[0], find_account_by_email(active_account)[1], find_account_by_email(active_account)[3])
    if(active_account == None):
        return render_template('login.html')
    if request.method == 'POST':
        email=(find_account_by_email(active_account)[0])
        if 'Background' in request.form:
            pub = request.form['infoProf']
            addBackground(email, str(pub))
            return redirect(url_for('index'))
        if 'Publications' in request.form:
            pub = request.form['infoProf']
            addPublication(email, str(pub))
            return redirect(url_for('index'))
        if 'Grants' in request.form:
            pub = request.form['infoProf']
            addGrants(email, str(pub))
            return redirect(url_for('index'))
        if 'Awards' in request.form:
            pub = request.form['infoProf']
            addAwards(email, str(pub))
            return redirect(url_for('index'))
        if 'Miscellaneous' in request.form:
            pub = request.form['infoProf']
            addMiss(email, str(pub))
            return redirect(url_for('index'))
        if 'Teaching' in request.form:
            pub = request.form['infoProf']
            addTeaching(email, str(pub))
            return redirect(url_for('index'))
        if 'PublicationsD' in request.form:
            pub = request.form['delete']
            try:
                pubI = int(pub)-1
                print(active_account)
                print(pubI)
                pubValue = find_account_by_email_by_mongo(active_account).publication[pubI]
                print(pubValue)
                deletePublication(active_account, pubValue)      
            except:
                return render_template('edit.html', error='Unvalid index')
            return redirect(url_for('index'))
        if 'GrantsD' in request.form:
            pub = request.form['delete']
            try:
                pubI = int(pub)-1
                pubValue = find_account_by_email_by_mongo(active_account).grants[pubI]
                deleteGrants(active_account, pubValue)      
            except:
                return render_template('edit.html', error='Unvalid index')
            return redirect(url_for('index'))
        if 'AwardsD' in request.form:
            pub = request.form['delete']
            try:
                pubI = int(pub)-1
                pubValue = find_account_by_email_by_mongo(active_account).awards[pubI]
                deleteAwards(active_account, pubValue)      
            except:
                return render_template('edit.html', error='Unvalid index')
            return redirect(url_for('index'))
        if 'MiscellaneousD' in request.form:
            pub = request.form['delete']
            try:
                pubI = int(pub)-1
                pubValue = find_account_by_email_by_mongo(active_account).miss[pubI]
                deleteMiss(active_account, pubValue)      
            except:
                return render_template('edit.html', error='Unvalid index')
            return redirect(url_for('index'))
        if 'TeachingD' in request.form:
            pub = request.form['delete']
            try:
                pubI = int(pub)-1
                pubValue = find_account_by_email_by_mongo(active_account).teaching[pubI]
                deleteTeaching(active_account, pubValue)
            except:
                return render_template('edit.html', error='Unvalid index')
            return redirect(url_for('index'))

        if 'PublicationsU' in request.form:
            pub = request.form['infoProf']
            ind = request.form['update']
            try:
                print(pub, ind)
                pubI = int(ind)-1
                print(pubI)
                pubValue = find_account_by_email_by_mongo(active_account).publication[pubI]
                print(pubValue)
                updatePublication(active_account, pub, pubValue)      
            except:
                return render_template('edit.html', error='Unvalid index')
            return redirect(url_for('index'))
        if 'GrantsU' in request.form:
            pub = request.form['infoProf']
            ind = request.form['update']
            try:
                pubI = int(ind)-1
                pubValue = find_account_by_email_by_mongo(active_account).grants[pubI]
                updateGrants(active_account, pub, pubValue)      
            except:
                return render_template('edit.html', error='Unvalid index')
            return redirect(url_for('index'))
        if 'AwardsU' in request.form:
            pub = request.form['infoProf']
            ind = request.form['update']
            try:
                pubI = int(ind)-1
                pubValue = find_account_by_email_by_mongo(active_account).awards[pubI]
                updateAwards(active_account, pub, pubValue)
            except:
                return render_template('edit.html', error='Unvalid index')
            return redirect(url_for('index'))
        if 'MiscellaneousU' in request.form:
            pub = request.form['infoProf']
            ind = request.form['update']
            try:
                pubI = int(ind)-1
                pubValue = find_account_by_email_by_mongo(active_account).miss[pubI]
                updateMiss(active_account, pub, pubValue)    
            except:
                return render_template('edit.html', error='Unvalid index')
            return redirect(url_for('index'))
        if 'TeachingU' in request.form:
            pub = request.form['infoProf']
            ind = request.form['update']
            try:
                pubI = int(ind)-1
                pubValue = find_account_by_email_by_mongo(active_account).teaching[pubI]
                updateTeaching(active_account, pub, pubValue)      
            except:
                return render_template('edit.html', error='Unvalid index')
            return redirect(url_for('index'))
        else:
            return render_template('edit.html', error= 'Error in the Request')
    return render_template('edit.html')         

@app.route('/show_faculty')
def showFaculty():
    global active_account
    if(active_account == None):
        return render_template('login.html')
    conn = connectgs()
    cur = conn.cursor()
    cur.execute("select * from faculty;")
    x = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('show_faculty.html', items=x)


@app.route('/show_crossfaculty')
def showCrossCut():
    global active_account
    if(active_account == None):
        return render_template('login.html')
    conn = connectgs()
    cur = conn.cursor()
    cur.execute("select * from crossfaculty;")
    x = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('showCrossCut.html', items=x)


@app.route('/show_hod')
def showHod():
    global active_account
    if(active_account == None):
        return render_template('login.html')
    conn = connectgs()
    cur = conn.cursor()
    cur.execute("select * from hod;")
    x = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('show_hod.html', items=x)


@app.route('/show_history_hod')
def show_history_hod():
    global active_account
    if(active_account == None):
        return render_template('login.html')
    conn = connectgs()
    cur = conn.cursor()
    cur.execute("select * from historyofhod;")
    x = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('show_historyOfHod.html', items=x)


@app.route('/show_history_cross')
def show_history_cross():
    global active_account
    if(active_account == None):
        return render_template('login.html')
    conn = connectgs()
    cur = conn.cursor()
    cur.execute("select * from historyofcrosscut;")
    x = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('showHistoryOfCrossCut.html', items=x)


@app.route('/show_approved_leaves',methods=['GET','POST'])
def show_approved_leaves():
    fid = []
    fid.append(request.args.get('type'))
    fid.append(request.args.get('type2'))
    con = connectgs()
    cur = con.cursor()
    cur.execute("select distinct leaveid,commenterid from comments where commenterid = '{}' and commenterpos = '{}'".format(fid[1],fid[0]))
    rows = cur.fetchall()
    rav = []
    for r in rows:
        l = r[0]
        cur.execute("select * from leaves where id = {} and (leavestatus=\'accepted\' or leavestatus=\'rejected\') and position = \'{}\'".format(l,fid[0]))
        if(cur.rowcount==1):
            fnt = cur.fetchone()
            rav.append([fnt[1],fnt[2],fnt[0]])
    return render_template('approved.html',posts=rav)


def find_account_by_email(email: str):
    #if not admin
    if(email!='admin@admin.com'):
        con = connectgs()
        cur = con.cursor()
        cur.execute('select * from faculty where id = \'{}\''.format(email))
        rows = cur.fetchall()
        old_account = rows
        cur.close()
        con.close()
        if(len(rows)!= 0):
            email = rows[0][0]
            Department = rows[0][2]
            name = rows[0][4]
            password = rows[0][5]
            return email, Department, name, password
        else:
            return 0
    else:
        #if admin
        con = connectgs()
        cur = con.cursor()
        cur.execute('select * from admin where id = \'{}\''.format(email))
        rows = cur.fetchall()
        old_account = rows
        cur.close()
        con.close()
        if(len(rows)!= 0):
            email = rows[0][0]
            password = rows[0][1]
            return email, password
        else:
            return 0


def create_account_by_flask(name, email, department, password):
    create_account_by_flask_mongo(email)
    print('created account', email)
    conn = connectgs()
    cur = conn.cursor()
    nLeaves = 50
    cur.execute("insert into faculty(ID, noOfLeaves, department, next_year_leaves,name, password) values (%s, %s, %s, %s,%s,  %s);  ", (str(email), int(nLeaves), str(department), int(nLeaves),str(name), str(password)))
    conn.commit()
    conn.close()

#### MongoDB #####
class Owner(mongoengine.Document):
    registered_date = mongoengine.DateTimeField(default=datetime.datetime.now)
    email = mongoengine.StringField(required=True)
    background = mongoengine.StringField()
    publication = mongoengine.ListField()
    grants = mongoengine.ListField()
    awards = mongoengine.ListField()
    teaching = mongoengine.ListField()
    miss = mongoengine.ListField()
    meta = {
        'db_alias': 'chor',
        'collection': 'owners'
    }

def create_account_by_flask_mongo(email) -> Owner:
    owner = Owner()
    owner.email = email
    owner.save()
    return owner

def find_account_by_email_by_mongo(email: str) -> Owner:
    owner = Owner.objects(email=email).first()
    return owner

def global_init():
    mongoengine.register_connection(alias='chor', name='faculty')


def updatePublication(emailid,  pub, pubValue):
    print("updatePublication")
    Owner.objects(email = emailid).update_one(pull__publication=pubValue)
    Owner.objects(email = emailid).update_one(push__publication=pub)

def updateGrants(emailid,  pub, pubValue):
    Owner.objects(email = emailid).update_one(pull__grants=pubValue)
    Owner.objects(email = emailid).update_one(push__grants=pub)
    
def updateAwards(emailid,  pub, pubValue):
    Owner.objects(email = emailid).update_one(pull__awards=pubValue)
    Owner.objects(email = emailid).update_one(push__awards=pub)
    
def updateTeaching(emailid,  pub, pubValue):
    Owner.objects(email = emailid).update_one(pull__teaching=pubValue)
    Owner.objects(email = emailid).update_one(push__teaching=pub)
    
def updateMiss(emailid,  pub, pubValue):
    Owner.objects(email = emailid).update_one(pull__miss=pubValue)
    Owner.objects(email = emailid).update_one(push__miss=pub)

def deletePublication(emailid, pub):
    print(emailid, pub)
    Owner.objects(email = emailid).update_one(pull__publication=pub)

def deleteGrants(emailid, pub):
    Owner.objects(email = emailid).update_one(pull__grants=pub)
    
def deleteAwards(emailid, pub):
    Owner.objects(email = emailid).update_one(pull__awards=pub)
    
def deleteTeaching(emailid, pub):
    Owner.objects(email = emailid).update_one(pull__teaching=pub)
    
def deleteMiss(emailid, pub):
    Owner.objects(email = emailid).update_one(pull__miss=pub)

def addBackground(emailid, pub):
    Owner.objects(email = emailid).update_one(set__background=pub)

def addPublication(emailid, pub):
    Owner.objects(email = emailid).update_one(push__publication=pub)

def addGrants(emailid, pub):
    Owner.objects(email = emailid).update_one(push__grants=pub)

def addAwards(emailid, pub):
    Owner.objects(email = emailid).update_one(push__awards=pub)

def addTeaching(emailid, pub):
    Owner.objects(email = emailid).update_one(push__teaching=pub)

def addMiss(emailid, pub):
    Owner.objects(email = emailid).update_one(push__miss=pub)

def getInfo(emailid):
    owner = find_account_by_email_by_mongo(emailid)
    info = {
        'background': owner.background,
        'publication': owner.publication,
        'grants': owner.grants,
        'awards': owner.awards,
        'teaching': owner.teaching,
        'miss': owner.miss
    }
    return info



if __name__ == '__main__':
    global_init()

    if (find_account_by_email('admin@admin.com')==0):
        password = 'admin@admin.com'
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        conn = connectgs()
        cur = conn.cursor()
        cur.execute("insert into admin(ID, password) values (%s, %s);  ", (str('admin@admin.com'), str(hashed.decode('utf-8'))))
        conn.commit()
        conn.close()
    
    app.run(debug=True)
