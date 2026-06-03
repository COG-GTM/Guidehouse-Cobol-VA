package com.cognition.jvdemo.db;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;

/** Port of the SQLCODE→DMS translation tests (DBIO.pco:374-398). */
class SqlCodeTranslatorTest {

    @Test void zeroIsOk() {
        assertEquals("0000", SqlCodeTranslator.translate(0));
    }

    @Test void hundredDefault() {
        assertEquals("0013", SqlCodeTranslator.translate(100));
    }

    @Test void hundredWithSetName() {
        assertEquals("0007", SqlCodeTranslator.translate(100, "X", "FIND"));
    }

    @Test void hundredWithSetNameButFetchOwnerReturnsDefault() {
        assertEquals("0013", SqlCodeTranslator.translate(100, "X", "FETCH OWNER"));
    }

    @Test void minusOne() {
        assertEquals("0005", SqlCodeTranslator.translate(-1));
    }

    @Test void minus8103LoggedAsOk() {
        assertEquals("0000", SqlCodeTranslator.translate(-8103));
    }

    @Test void otherReturns9999() {
        assertEquals("9999", SqlCodeTranslator.translate(-42));
        assertEquals("9999", SqlCodeTranslator.translate(1000));
    }
}
