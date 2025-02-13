<node name="snmp-exporter">
  <properties>
    <help>Prometheus exporter for ping target IP metrics</help>
  </properties>
  <children>
    #include <include/listen-address.xml.i>
    #include <include/port-number.xml.i>
    <leafNode name="port">
      <defaultValue>9116</defaultValue>
    </leafNode>
    <tagNode name="auth">
      <properties>
        <help>auth name for community to snmp-exporter.</help>
      </properties>
      <children>
        <leafNode name="community">
          <properties>
            <help>snmp community.</help>
          </properties>
        </leafNode>
      </children>
    </tagNode>
  </children>
</node>
