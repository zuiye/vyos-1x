<node name="ping-exporter">
  <properties>
    <help>Prometheus exporter for ping target IP metrics</help>
  </properties>
  <children>
    #include <include/listen-address.xml.i>
    #include <include/port-number.xml.i>
    <leafNode name="port">
      <defaultValue>9427</defaultValue>
    </leafNode>

    <leafNode name="interval">
      <properties>
        <help>Interval for ICMP echo requests</help>
        <valueHelp>
          <format>u32:1-65535</format>
          <description>Interval for ICMP echo requests, 1s to 65535s</description>
        </valueHelp>
        <constraint>
          <validator name="numeric" argument="--range 1-65535"/>
        </constraint>
        <constraintErrorMessage>Interval for ICMP echo requests must be in range 1s to 65535s</constraintErrorMessage>
      </properties>
    </leafNode>
    <leafNode name="interval">
      <defaultValue>10</defaultValue>
    </leafNode>

    <leafNode name="timeout">
      <properties>
        <help>Timeout for ICMP echo request</help>
        <valueHelp>
          <format>u32:1-65535</format>
          <description>Timeout for ICMP echo request, 1s to 65535s</description>
        </valueHelp>
        <constraint>
          <validator name="numeric" argument="--range 1-65535"/>
        </constraint>
        <constraintErrorMessage>Timeout for ICMP echo request must be in range 1s to 65535s</constraintErrorMessage>
      </properties>
    </leafNode>
    <leafNode name="timeout">
      <defaultValue>2</defaultValue>
    </leafNode>
    <leafNode name="history-size">
      <properties>
        <help>Number of results to remember per target</help>
        <valueHelp>
          <format>u32:1-65535</format>
          <description>Number of results to remember per target</description>
        </valueHelp>
        <constraint>
          <validator name="numeric" argument="--range 1-65535"/>
        </constraint>
        <constraintErrorMessage>Number of results to remember per target</constraintErrorMessage>
      </properties>
    </leafNode>
    <leafNode name="history-size">
      <defaultValue>10</defaultValue>
    </leafNode>
    <leafNode name="ping-size">
      <properties>
        <help>Payload size for ICMP echo requests</help>
        <valueHelp>
          <format>u32:1-65535</format>
          <description>Payload size for ICMP echo requests</description>
        </valueHelp>
        <constraint>
          <validator name="numeric" argument="--range 1-65535"/>
        </constraint>
        <constraintErrorMessage>Payload size for ICMP echo requests</constraintErrorMessage>
      </properties>
    </leafNode>
    <leafNode name="ping-size">
      <defaultValue>56</defaultValue>
    </leafNode>

    <tagNode name="target">
      <properties>
        <help>Ping-exporter target IP.</help>
        <valueHelp>
          <format>ipv4</format>
          <description>IPv4 address</description>
        </valueHelp>
        <valueHelp>
          <format>ipv6</format>
          <description>IPv6 address</description>
        </valueHelp>
        <constraint>
          <validator name="ip-address"/>
        </constraint>
      </properties>
      <children>
        <tagNode name="label">
          <properties>
            <help>Label name to Ping-exporter target IP</help>
          </properties>
          <children>
            <leafNode name="value">
              <properties>
                <help>The value for Label name to Ping-exporter target IP.</help>
              </properties>
            </leafNode>

          </children>
        </tagNode>
      </children>
    </tagNode>

  </children>
</node>
