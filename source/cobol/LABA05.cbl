       IDENTIFICATION DIVISION. 
       PROGRAM-ID.                 LABA05.  
MIGRTN*----------------------------------------------------------*
MIGRTN*  PROGRAM CONVERTED BY INFORMATION ANALYSIS INCORPORATED  *
MIGRTN*  DATE:  10/31/2012     TIME:  13:55:30                   *
MIGRTN*----------------------------------------------------------*
       DATE-COMPILED.   
      * 
      ******************************************************************
      * 
      * Programmer: Daniel Lee  
      * Date-Written: Jan 4, 95 
      * 
      * Remarks: This program is to reset the JV-NUMBER on  
      *          JV-CONTROL-REC (DMS) to 1 every fiscal year.   
      * 
      * Input DMS:  JV-CONTROL-REC  
      * 
      ******************************************************************
      * *                                                            * *
      * *              PROGRAMMER'S SUMMARY OF JV SYSTEM             * *
      * *   ------------------------------------------------------   * *
      * *   See LABS01                                               * *
      * * * * * * * * * * * * * * * * ** * * * * * * * * * * * * * * * *
      *                                                                *
      *                 INVENTORY OF CHANGES TO LABR06                 *
      *                                                                *
      *   *   *   *   *   *   *   *   *    *   *   *   *   *   *   *   *
      *                                                                *
      * CHANGE  CHANGE   CHANGED  PROJECT                              *
      * NUMBER   DATE      BY       ID          NATURE OF CHANGE       *
      *------- -------- --------- ------- ---------------------------- *
      *CHG-000 MM/DD/YY YOURNAME          SUMMARIZE YOUR CHANGES HERE  *CHG-000 
      *CHG-001 12/21/98 J. COLE   990133  ADDED BINARY STATEMENT TO    *CHG-001 
      *                                   TELL COMPILER PROGRAM IS     *CHG-001 
      *                                   UCOB PROGRAM NOT ACOB.       *CHG-001 
      ******************************************************************
    
       ENVIRONMENT DIVISION.
       CONFIGURATION SECTION.   
MIGRTN*SOURCE-COMPUTER.        UNISYS-2200. 
MIGRTN*OBJECT-COMPUTER.        UNISYS-2200. 
MIGRTN*SPECIAL-NAMES.          PRINTER IS PRINTER.  
    
       INPUT-OUTPUT SECTION.
       DATA DIVISION.   
MIGRTN*SUBSCHEMA SECTION.   
MIGRTN*INVOKE SUBSCHEMA UJV-SUB IN FILE SCHEMAFILE  
MIGRTN*        OF SCHEMA JV-SCHEMA 
MIGRTN*        KEY FOR INVOKE IS 'JVSYS'
MIGRTN*        COPYING RECORDS INTO WORKING 
MIGRTN*        COPYING DATA-NAMES INTO WORKING  
MIGRTN*        RUN-UNIT-ID IS INITJV
MIGRTN*        DMCA AND RUN-UNIT-STATISTICS ARE WORKING 
MIGRTN*        ROLLBACK IS DML-ROLLBACK-PARA.   
       FILE SECTION.
    
       WORKING-STORAGE SECTION. 
MIGRTN COPY DBVAR.
MIGRTN COPY DMCA. 
MIGRTN COPY JV-CONTROL-REC.
       01  JV-NUMBER-WS                  PIC 9(6).  
    
MIGRTN*01  THISPGMISUCOB                 PIC 1(36) BINARY-1.            CHG-001 
MIGRTN 01  THISPGMISUCOB                 PIC 9(04).                     CHG-001 

       PROCEDURE DIVISION.  
MIGRTN*    CALL 'CBL_DEBUGBREAK'.                                     
MIGRTN     MOVE 'CONNECT' TO DB-FUNCTION                              
MIGRTN     INITIALIZE DB-FUNCTION-TYPE, DB-TABLE-NAME, DB-DATA        
MIGRTN     CALL 'DBIO' USING DB-DMSREC-NAME                           
MIGRTN                       DB-FUNCTION                  
MIGRTN                       DB-FUNCTION-TYPE             
MIGRTN                       DB-SET-NAME                  
MIGRTN                       DB-DATA                      
MIGRTN                       DB-ROWID                     
MIGRTN                       DB-MISC                      
MIGRTN                       DB-RETURN-CODE               
MIGRTN                       DB-MESSAGE                   
MIGRTN     PERFORM DMCA-ERRFLDS THRU DMCA-ERRFLDS-EXIT
MIGRTN     IF NOT DB-OK                                               
MIGRTN         DISPLAY '*** PROGRAM ABORTED DUE TO CONNECT ERROR***'  
MIGRTN         MOVE 99 TO RETURN-CODE
MIGRTN         STOP RUN                                               
MIGRTN     END-IF.                                                    

       0000-MAIN-LINE.  
      *    MOVE 1 TO MCFLAG.
MIGRTN*    PERFORM DML-IMPART.  
MIGRTN*    PERFORM OPEN-JV-DB-UPDATE.   
           PERFORM FETCH-CTRL-REC.  
           IF ERROR-NUM EQUAL '0000'
               PERFORM MODIFY-CTRL-REC  
           ELSE 
               DISPLAY 'Unable FETCH JV-CONTROL-REC' UPON PRINTER   
MIGRTN*        CALL 'ABORTRUN'  
MIGRTN         MOVE 99 TO RETURN-CODE
MIGRTN         STOP RUN
           END-IF.  
MIGRTN*    PERFORM JV-DML-RUN-INFO. 
    
       END-PROGRAM. 
MIGRTN*    IF IMPART-COUNT EQUAL 1  
MIGRTN*          PERFORM CLOSE-DEPART-DB.   
           STOP RUN.
    
      / 
    
MIGRTN*DML-IMPART.  
MIGRTN*    MOVE 'JV' TO DB-IMPART-KEY. 
MIGRTN*    MOVE 'JV268ONE' TO JV-EXCLUSIVE-RETRIEVAL-KEY.   
MIGRTN*    MOVE 'JV268CHG' TO JV-UPDATE-KEY.
MIGRTN*    MOVE 'DMLMDD0268L1' TO JV-AREA-NAME. 
MIGRTN*    MOVE 'JVTRANDEL' TO JV-DELETE-KEY.   
MIGRTN*    MOVE 'JV' TO DB-ACCESS-KEY. 
MIGRTN*    IMPART.  
MIGRTN*    IF ERROR-NUM NOT EQUAL '0000'
MIGRTN*        DISPLAY 'ERROR ON IMPART DB' UPON PRINTER.   
    
       CLOSE-DEPART-DB. 
MIGRTN*    CLOSE ALL.   
MIGRTN*    IF ERROR-NUM NOT EQUAL '0000'
MIGRTN*        DISPLAY 'ERROR ON CLOSE DB' UPON PRINTER.
MIGRTN*    DEPART.  
MIGRTN     INITIALIZE                            DB-DMSREC-NAME       
MIGRTN     MOVE 'COMMIT'                      TO DB-FUNCTION          
MIGRTN     MOVE 'DEPART'                      TO DB-FUNCTION-TYPE     
MIGRTN     INITIALIZE                            DB-SET-NAME          
MIGRTN     CALL 'DBIO' USING DB-DMSREC-NAME                           
MIGRTN                       DB-FUNCTION                  
MIGRTN                       DB-FUNCTION-TYPE             
MIGRTN                       DB-SET-NAME                  
MIGRTN                       DB-DATA                      
MIGRTN                       DB-ROWID                     
MIGRTN                       DB-MISC                      
MIGRTN                       DB-RETURN-CODE               
MIGRTN                       DB-MESSAGE                   
MIGRTN     PERFORM DMCA-ERRFLDS THRU DMCA-ERRFLDS-EXIT.
           IF ERROR-NUM NOT EQUAL '0000'
               DISPLAY 'ERROR ON DEPART DB' UPON PRINTER.   
    
MIGRTN*OPEN-JV-DB-UPDATE.   
MIGRTN*    OPEN JV-AREA-NAME USAGE-MODE IS UPDATE.  
MIGRTN*    IF ERROR-NUM NOT EQUAL '0000'
MIGRTN*        DISPLAY ' ERROR OPEN AREA 268L1 ' UPON PRINTER   
MIGRTN*    ELSE 
MIGRTN*        MOVE 1 TO PAGE-NUM   OF JV-AREA-KEY  
MIGRTN*        MOVE 1 TO RECORD-NUM OF JV-AREA-KEY. 
    
       FETCH-CTRL-REC.  
MIGRTN*    FETCH JV-AREA-KEY JV-AREA-NAME.  
MIGRTN     MOVE 'JV-CONTROL-REC'              TO DB-DMSREC-NAME 
MIGRTN     MOVE 'SELECT'                      TO DB-FUNCTION          
MIGRTN     MOVE 'FETCH'                       TO DB-FUNCTION-TYPE     
MIGRTN     INITIALIZE                            DB-SET-NAME          
MIGRTN     MOVE JV-CONTROL-REC                TO DB-DATA              
MIGRTN     CALL 'DBIO' USING DB-DMSREC-NAME                           
MIGRTN                       DB-FUNCTION                  
MIGRTN                       DB-FUNCTION-TYPE             
MIGRTN                       DB-SET-NAME                  
MIGRTN                       DB-DATA                      
MIGRTN                       DB-ROWID                     
MIGRTN                       DB-MISC                      
MIGRTN                       DB-RETURN-CODE               
MIGRTN                       DB-MESSAGE                   
MIGRTN     PERFORM DMCA-ERRFLDS THRU DMCA-ERRFLDS-EXIT.
MIGRTN     IF DB-OK                               
MIGRTN         MOVE DB-DATA  TO JV-CONTROL-REC    
MIGRTN         MOVE DB-ROWID TO 287-ROWID         
MIGRTN     END-IF                                 
           IF ERROR-NUM NOT EQUAL '0000'
               DISPLAY 'ERROR ON FETCH CONTROL REC' UPON PRINTER
           ELSE 
               DISPLAY 'FETCHED CONTROL REC' UPON PRINTER.  
    
       MODIFY-CTRL-REC. 
           DISPLAY 'Before modification: ' UPON PRINTER.
           PERFORM 9999-DISPLAY-REC THRU 9999-DISPLAY-REC-X.
           MOVE 1   TO JV-NUMBER.   
MIGRTN*    MODIFY JV-CONTROL-REC RECORD.
MIGRTN     MOVE 'JV-CONTROL-REC'              TO DB-DMSREC-NAME       
MIGRTN     MOVE 'UPDATE'                      TO DB-FUNCTION          
MIGRTN     MOVE 'MODIFY'                      TO DB-FUNCTION-TYPE     
MIGRTN     INITIALIZE                            DB-SET-NAME          
MIGRTN     MOVE JV-CONTROL-REC                TO DB-DATA              
MIGRTN     CALL 'DBIO' USING DB-DMSREC-NAME                           
MIGRTN                       DB-FUNCTION                  
MIGRTN                       DB-FUNCTION-TYPE             
MIGRTN                       DB-SET-NAME                  
MIGRTN                       DB-DATA                      
MIGRTN                       DB-ROWID                     
MIGRTN                       DB-MISC                      
MIGRTN                       DB-RETURN-CODE               
MIGRTN                       DB-MESSAGE                   
MIGRTN     PERFORM DMCA-ERRFLDS THRU DMCA-ERRFLDS-EXIT.
           IF ERROR-NUM NOT EQUAL '0000'
               DISPLAY 'ERROR ON MODIFY CONTROL REC' UPON PRINTER   
MIGRTN*        CALL 'ABORTRUN'  
MIGRTN         MOVE 99 TO RETURN-CODE
MIGRTN         STOP RUN
           ELSE 
               DISPLAY ' ' UPON PRINTER 
               DISPLAY 'After modification: ' UPON PRINTER  
               PERFORM 9999-DISPLAY-REC THRU 9999-DISPLAY-REC-X 
           END-IF.  
    
       DML-ROLLBACK-PARA.   
MIGRTN*    PERFORM JV-DML-RUN-INFO. 
MIGRTN*    IF DEPART-COUNT EQUAL ZEROS  
MIGRTN*       AND IMPART-COUNT EQUAL 1  
MIGRTN*            CLOSE ALL
MIGRTN*            DEPART WITH ROLLBACK 
MIGRTN             INITIALIZE                    DB-DMSREC-NAME       
MIGRTN             MOVE 'ROLLBACK'            TO DB-FUNCTION          
MIGRTN             MOVE 'DEPART'              TO DB-FUNCTION-TYPE     
MIGRTN             INITIALIZE                    DB-SET-NAME          
MIGRTN             CALL 'DBIO' USING DB-DMSREC-NAME                   
MIGRTN                               DB-FUNCTION          
MIGRTN                               DB-FUNCTION-TYPE     
MIGRTN                               DB-SET-NAME          
MIGRTN                               DB-DATA              
MIGRTN                               DB-ROWID             
MIGRTN                               DB-MISC              
MIGRTN                               DB-RETURN-CODE       
MIGRTN                               DB-MESSAGE           
MIGRTN             PERFORM DMCA-ERRFLDS THRU DMCA-ERRFLDS-EXIT
                   DISPLAY ' PROGRAM  ERROR OFF ' UPON PRINTER. 
           STOP RUN.
    
MIGRTN*JV-DML-RUN-INFO. 
MIGRTN*    DISPLAY 'OPEN COUNT.........' OPEN-COUNT      UPON PRINTER.  
MIGRTN*    DISPLAY 'CLOSE COUNT........' CLOSE-COUNT     UPON PRINTER.  
MIGRTN*    DISPLAY 'GET COUNT..........' GET-COUNT       UPON PRINTER.  
MIGRTN*    DISPLAY 'FIND COUNT.........' FIND-COUNT   UPON PRINTER. 
MIGRTN*    DISPLAY 'DELETE COUNT.......' DELETE-COUNT UPON PRINTER. 
MIGRTN*    DISPLAY 'FREE COUNT.........' FREE-COUNT      UPON PRINTER.  
MIGRTN*    DISPLAY 'KEEP COUNT.........' KEEP-COUNT      UPON PRINTER.  
MIGRTN*    DISPLAY 'INSERT COUNT.......' INSERT-COUNT UPON PRINTER. 
MIGRTN*    DISPLAY 'MODIFY COUNT.......' MODIFY-COUNT UPON PRINTER. 
MIGRTN*    DISPLAY 'REMOVE COUNT.......' REMOVE-COUNT UPON PRINTER. 
MIGRTN*    DISPLAY 'STORE COUNT........' STORE-COUNT  UPON PRINTER. 
MIGRTN*    DISPLAY 'IMPART COUNT.......' IMPART-COUNT    UPON PRINTER.  
MIGRTN*    DISPLAY 'DEPART COUNT.......' DEPART-COUNT    UPON PRINTER.  
MIGRTN*    DISPLAY 'IF COUNT...........' IF-COUNT        UPON PRINTER.  
MIGRTN*    DISPLAY 'MOVE COUNT.........' MOVE-COUNT      UPON PRINTER.  
MIGRTN*    DISPLAY 'LOG COUNT..........' LOG-COUNT       UPON PRINTER.  
MIGRTN*    DISPLAY 'ACQUIRE-COUNT......' ACQUIRE-COUNT   UPON PRINTER.  
MIGRTN*    DISPLAY 'RUN UNIT ID........' RUN-UNIT-ID     UPON PRINTER.  
MIGRTN*    DISPLAY 'RUN UNIT PRIORITY..' PRIORITY        UPON PRINTER.  
MIGRTN*    DISPLAY 'IMPART/DEPART CD...' IMPART-DEPART   UPON PRINTER.  
MIGRTN*    DISPLAY 'COMMAND SEQ NR.....' COMMAND-SEQ-NUM UPON PRINTER.  
MIGRTN*    DISPLAY 'AREA NAME..........' AREA-NAME       UPON PRINTER.  
MIGRTN*    DISPLAY 'AREA KEY...........' PAGE-NUM   OF AREA-KEY 
MIGRTN*                                  RECORD-NUM OF AREA-KEY 
MIGRTN*                                                  UPON PRINTER.  
MIGRTN*    DISPLAY 'RECORD-NAME........' RECORD-NAME     UPON PRINTER.  
MIGRTN*    DISPLAY 'RECORD-NAME........' DB-DMSREC-NAME     UPON PRINTER.  
MIGRTN*    DISPLAY 'DATABASE-KEY.......' DATABASE-KEY    UPON PRINTER.  
MIGRTN*    DISPLAY 'ERROR AREA NAME....' ERROR-AREA      UPON PRINTER.  
MIGRTN*    DISPLAY 'ERROR RECORD NAME..' ERROR-RECORD    UPON PRINTER.  
MIGRTN*    DISPLAY 'ERROR SET NAME.....' ERROR-SET       UPON PRINTER.  
MIGRTN*    DISPLAY 'RB ERROR CD........' RB-ERROR-CODE   UPON PRINTER.  
MIGRTN*    DISPLAY 'ERROR FUNCTION.....' ERROR-FUNCTION  UPON PRINTER.  
MIGRTN*    DISPLAY 'DMR ERROR CD.......' ERROR-NUM       UPON PRINTER.  
MIGRTN*    DISPLAY 'IO ERROR STATUS....' IO-ERROR-STATUS UPON PRINTER.  
MIGRTN*    DISPLAY 'QUEUE ERROR CD.....' QUEUE-ERR-STATUS UPON PRINTER. 
MIGRTN*    DISPLAY 'DMR LEVEL NR.......' DMR-LEV-NUM     UPON PRINTER.  
MIGRTN*    DISPLAY 'CUR AREA NAME..' CURRENT-AREA-NAME UPON PRINTER.
MIGRTN*    DISPLAY 'CURRENT AREA KEY...' PAGE-NUM   OF CURRENT-AREA-KEY 
MIGRTN*                                  RECORD-NUM OF CURRENT-AREA-KEY 
MIGRTN*                                                  UPON PRINTER.  
MIGRTN*    DISPLAY 'DATABASE KEY.......' DATABASE-KEY    UPON PRINTER.  
    
       9999-DISPLAY-REC.
           DISPLAY 'JV-CONTROL-1 = ' JV-CONTROL-1 UPON PRINTER. 
           DISPLAY 'JV-CONTROL-2 = ' JV-CONTROL-2 UPON PRINTER. 
           DISPLAY 'JV-CONTROL-3 = ' JV-CONTROL-3 UPON PRINTER. 
           DISPLAY 'JV-CONTROL-4 = ' JV-CONTROL-4 UPON PRINTER. 
           DISPLAY 'JV-CONTROL-5 = ' JV-CONTROL-5 UPON PRINTER. 
           MOVE JV-NUMBER TO JV-NUMBER-WS.  
           DISPLAY 'JV-NUMBER    = ' JV-NUMBER-WS UPON PRINTER. 
       9999-DISPLAY-REC-X.  
           EXIT.

MIGRTN COPY DMCAERR.
