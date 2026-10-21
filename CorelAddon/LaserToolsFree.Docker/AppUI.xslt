<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:frmwrk="Corel Framework Data">
  <xsl:output method="xml" encoding="UTF-8" indent="yes"/>
  <frmwrk:uiconfig>
    <frmwrk:applicationInfo userConfiguration="true" />
  </frmwrk:uiconfig>
  <xsl:template match="node()|@*">
    <xsl:copy><xsl:apply-templates select="node()|@*"/></xsl:copy>
  </xsl:template>
  <xsl:template match="uiConfig/items">
    <xsl:copy>
      <xsl:apply-templates select="node()|@*"/>
      <itemData guid="b4e1c580-9389-4985-a754-b48e22df009a" noBmpOnMenu="true"
                type="checkButton" check="*Docker('b997cf9e-09a1-4d3b-848b-bd3812d4b7cb')"
                userCaption="Laser Tools Free" enable="true" />
      <itemData guid="4214ea9a-e17a-4dca-9172-131695deefdd"
                type="wpfhost" hostedType="Addons\LaserToolsFree\LaserToolsFree.Docker.dll,LaserToolsFree.Docker.DockerUI"
                enable="true" />
    </xsl:copy>
  </xsl:template>
  <xsl:template match="uiConfig/dockers">
    <xsl:copy>
      <xsl:apply-templates select="node()|@*"/>
      <dockerData guid="b997cf9e-09a1-4d3b-848b-bd3812d4b7cb"
                  userCaption="Laser Tools Free" wantReturn="true" focusStyle="noThrow">
        <container>
          <item dock="fill" margin="0,0,0,0" guidRef="4214ea9a-e17a-4dca-9172-131695deefdd" />
        </container>
      </dockerData>
    </xsl:copy>
  </xsl:template>
</xsl:stylesheet>
