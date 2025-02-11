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
  </children>
</node>
